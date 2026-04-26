import json
from dataclasses import dataclass
from datetime import datetime, timezone
from html import escape
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
    status_color = "#b7f84a" if report.status == "success" else "#ff7676"
    fields = [
        ("Status", report.status),
        ("Template", report.template),
        ("Timesteps", f"{report.steps or 0:,}"),
        ("Episodes", str(report.episodes or 0)),
        ("Average reward", f"{report.mean_return:.3f}" if report.mean_return is not None else "n/a"),
        ("Success rate", f"{report.best_return:.3f}" if report.best_return is not None else "n/a"),
    ]
    secondary = [
        ("Checkpoint", report.checkpoint_uri or "n/a"),
        ("Dashboard", report.artifact_links.get("dashboard") if report.artifact_links else None),
    ]
    metric_rows = "".join(
        "<tr>"
        + "".join(
            f"""
            <td style="width:50%;padding:14px 16px;border-top:1px solid #27313a;vertical-align:top;">
              <div style="font-size:10px;letter-spacing:1.8px;text-transform:uppercase;color:#98a69a;">{escape(label)}</div>
              <div style="margin-top:5px;font-size:16px;font-weight:700;color:#f4f7ef;word-break:break-word;">{escape(value)}</div>
            </td>
            """
            for label, value in fields[index : index + 2]
        )
        + "</tr>"
        for index in range(0, len(fields), 2)
    )
    secondary_rows = "".join(
        f"""
        <tr>
          <td style="padding:8px 0;font-size:11px;letter-spacing:1.6px;text-transform:uppercase;color:#98a69a;width:120px;">{escape(label)}</td>
          <td style="padding:8px 0;font-size:13px;color:#c4cec2;word-break:break-word;">{escape(value or "n/a")}</td>
        </tr>
        """
        for label, value in secondary
    )

    return (
        '<div style="margin:0;background:#090b0d;padding:28px;font-family:Inter,Arial,sans-serif;color:#f4f7ef;">'
        '<div style="max-width:680px;margin:0 auto;border:1px solid #27313a;border-radius:12px;overflow:hidden;background:#11161a;">'
        '<div style="padding:24px 26px;border-bottom:1px solid #27313a;">'
        '<div style="font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#98a69a;">Hermes Run Report</div>'
        f'<h1 style="margin:10px 0 0;font-size:28px;line-height:1.18;color:#f4f7ef;">{escape(report.run_id)}</h1>'
        f'<p style="margin:14px 0 0;font-size:15px;line-height:1.65;color:#c4cec2;">{escape(report.model_summary)}</p>'
        f'<div style="display:inline-block;margin-top:16px;padding:5px 10px;border-radius:999px;background:rgba(183,248,74,0.12);color:{status_color};font-size:12px;font-weight:700;">{escape(report.status)}</div>'
        "</div>"
        '<table role="presentation" cellspacing="0" cellpadding="0" style="width:100%;border-collapse:collapse;">'
        f"{metric_rows}"
        "</table>"
        '<div style="padding:20px 26px;border-top:1px solid #27313a;">'
        '<table role="presentation" cellspacing="0" cellpadding="0" style="width:100%;border-collapse:collapse;">'
        f"{secondary_rows}"
        "</table>"
        "</div>"
        "</div>"
        "</div>"
    )


def _configured_recipients() -> list[str]:
    if config.REPORT_RECIPIENT_EMAILS:
        return list(config.REPORT_RECIPIENT_EMAILS)
    if config.AGENTMAIL_INBOX_ID:
        return [config.AGENTMAIL_INBOX_ID]
    return []


def _normalize_recipients(recipient: Optional[object]) -> list[str]:
    if recipient is None:
        return _configured_recipients()
    if isinstance(recipient, str):
        parsed = [addr.strip() for addr in recipient.split(",") if addr.strip()]
        return parsed or _configured_recipients()
    if isinstance(recipient, (list, tuple, set)):
        parsed = [str(addr).strip() for addr in recipient if str(addr).strip()]
        return parsed or _configured_recipients()
    return _configured_recipients()


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


def send_report(report: RunReport, recipient: Optional[object] = None) -> AgentMailResult:
    targets = _normalize_recipients(recipient)
    if not config.AGENTMAIL_API_KEY or not config.AGENTMAIL_INBOX_ID or not targets:
        return AgentMailResult(delivery_status="skipped", error="AgentMail is not configured")

    body = {
        "to": targets,
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
