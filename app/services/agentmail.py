import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote
from urllib import error, request

from app import config
from app.schemas.agentmail import AgentMailMessageDetail, AgentMailMessageList, AgentMailMessageSummary
from app.schemas.run import RunReport


@dataclass
class AgentMailResult:
    delivery_status: str
    message_id: Optional[str] = None
    thread_id: Optional[str] = None
    error: Optional[str] = None


def _html_report(report: RunReport) -> str:
    return (
        f"<h1>Hermes Run Report: {report.run_id}</h1>"
        f"<p>{report.model_summary}</p>"
        "<ul>"
        f"<li>Status: {report.status}</li>"
        f"<li>Template: {report.template}</li>"
        f"<li>Mean return: {report.mean_return}</li>"
        f"<li>Best return: {report.best_return}</li>"
        f"<li>Checkpoint: {report.checkpoint_uri or 'n/a'}</li>"
        "</ul>"
    )


def _configured_recipient() -> str:
    return config.REPORT_RECIPIENT_EMAIL or config.AGENTMAIL_INBOX_ID


def _request_json(method: str, path: str, body: Optional[dict] = None) -> dict:
    if not config.AGENTMAIL_API_KEY or not config.AGENTMAIL_INBOX_ID:
        raise RuntimeError("AgentMail is not configured")

    url = f"{config.AGENTMAIL_API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    payload = json.dumps(body).encode("utf-8") if body is not None else None
    req = request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {config.AGENTMAIL_API_KEY}",
            "Accept": "application/json",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
        method=method,
    )

    try:
        with request.urlopen(req, timeout=15) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AgentMail HTTP {exc.code}: {detail}") from exc
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc

    return json.loads(raw or "{}")


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if value is None:
        return []
    return [str(value)]


def _message_summary(data: dict) -> AgentMailMessageSummary:
    normalized = {
        **data,
        "labels": _as_list(data.get("labels")),
        "to": _as_list(data.get("to")),
        "cc": _as_list(data.get("cc")),
        "bcc": _as_list(data.get("bcc")),
    }
    return AgentMailMessageSummary.model_validate(normalized)


def send_report(report: RunReport) -> AgentMailResult:
    recipient = _configured_recipient()
    if not config.AGENTMAIL_API_KEY or not config.AGENTMAIL_INBOX_ID or not recipient:
        return AgentMailResult(delivery_status="skipped", error="AgentMail is not configured")

    body = {
        "to": [recipient],
        "subject": f"[RL] run {report.run_id} {report.status}",
        "text": report.markdown,
        "html": _html_report(report),
        "labels": ["hermes", "run-report", report.status],
    }
    try:
        data = _request_json("POST", f"inboxes/{config.AGENTMAIL_INBOX_ID}/messages/send", body)
    except Exception as exc:
        return AgentMailResult(delivery_status="failed", error=str(exc))

    return AgentMailResult(
        delivery_status="sent",
        message_id=data.get("id") or data.get("message_id"),
        thread_id=data.get("thread_id") or data.get("threadId"),
    )


def list_inbox_messages(limit: int = 25) -> AgentMailMessageList:
    data = _request_json("GET", f"inboxes/{config.AGENTMAIL_INBOX_ID}/messages?limit={limit}")
    messages = [_message_summary(item) for item in data.get("messages", [])]
    return AgentMailMessageList(
        count=int(data.get("count") or len(messages)),
        messages=messages,
        next_page_token=data.get("next_page_token") or data.get("nextPageToken"),
    )


def get_inbox_message(message_id: str) -> AgentMailMessageDetail:
    safe_message_id = quote(message_id, safe="")
    data = _request_json("GET", f"inboxes/{config.AGENTMAIL_INBOX_ID}/messages/{safe_message_id}")
    summary = _message_summary(data).model_dump(by_alias=True)
    return AgentMailMessageDetail.model_validate(
        {
            **summary,
            "text": data.get("text"),
            "html": data.get("html"),
            "extracted_text": data.get("extracted_text") or data.get("extractedText"),
            "extracted_html": data.get("extracted_html") or data.get("extractedHtml"),
            "attachments": data.get("attachments") or [],
            "raw": data,
        }
    )


def build_mock_run_report() -> RunReport:
    created_at = datetime.now(timezone.utc).isoformat()
    stamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    run_id = f"run_mock_{stamp}"
    steps = 30000
    episodes = 10
    mean_return = 38.4
    best_return = 0.7
    template = "roomba.room-10.0.dirt-3"
    dashboard_url = f"{config.HERMES_PUBLIC_BASE_URL.rstrip('/')}/runs/{run_id}"
    model_summary = (
        f"PPO run {run_id} finished with status success. "
        f"Trained for {steps:,} timesteps and evaluated across {episodes} episodes. "
        f"Average reward: {mean_return:.3f}; success rate: {best_return:.3f}."
    )
    markdown = "\n".join(
        [
            f"# Hermes Run Report: {run_id}",
            "",
            "- Status: `success`",
            f"- Template: `{template}`",
            f"- Timesteps: `{steps}`",
            f"- Episodes: `{episodes}`",
            f"- Average reward: `{mean_return}`",
            f"- Success rate: `{best_return}`",
            f"- Dashboard: {dashboard_url}",
            "",
            model_summary,
        ]
    )
    return RunReport(
        run_id=run_id,
        status="success",
        started_at=created_at,
        ended_at=created_at,
        duration_sec=872.0,
        template=template,
        algo="PPO",
        config={
            "total_timesteps": steps,
            "eval_episodes": episodes,
            "seed": 42,
            "room_size": 10.0,
            "max_steps": 200,
            "dirt_count": 3,
        },
        steps=steps,
        episodes=episodes,
        mean_return=mean_return,
        best_return=best_return,
        checkpoint_uri=f"runs/{run_id}/model/roomba_policy.zip",
        artifact_links={"dashboard": dashboard_url},
        model_summary=model_summary,
        markdown=markdown,
        created_at=created_at,
    )
