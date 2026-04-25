import json
from dataclasses import dataclass
from typing import Optional
from urllib import error, request

from app import config
from app.schemas.agentmail import AgentMailMessageDetail, AgentMailMessageList, AgentMailMessageSummary
from app.schemas.run import RunReport
from app.services.reports import is_historical_agentmail_seed, list_agentmail_reports, resolve_report


@dataclass
class AgentMailResult:
    delivery_status: str
    message_id: Optional[str] = None
    thread_id: Optional[str] = None
    error: Optional[str] = None


LOCAL_INBOX_ID = "hermes-local-feed"
LOCAL_FROM_ADDRESS = "hermes@local.agentmail"
LOCAL_TO_ADDRESS = "runs@local.agentmail"


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


def _message_id(run_id: str) -> str:
    return f"run:{run_id}"


def _message_source(report: RunReport) -> str:
    if is_historical_agentmail_seed(report.run_id):
        return "historical_seed"
    return "run_report"


def _message_labels(report: RunReport) -> list[str]:
    freshness = "historical" if _message_source(report) == "historical_seed" else "live"
    return ["hermes", "run-report", report.status, freshness]


def _message_summary(report: RunReport) -> AgentMailMessageSummary:
    timestamp = report.ended_at or report.created_at
    recipient = _configured_recipient() or LOCAL_TO_ADDRESS
    source = _message_source(report)
    message_id = _message_id(report.run_id)
    return AgentMailMessageSummary(
        inbox_id=LOCAL_INBOX_ID,
        message_id=message_id,
        source=source,
        run_id=report.run_id,
        thread_id=message_id,
        external_message_id=report.agentmail_message_id,
        external_thread_id=report.agentmail_thread_id,
        labels=_message_labels(report),
        timestamp=timestamp,
        created_at=report.created_at,
        updated_at=report.created_at,
        from_address=LOCAL_FROM_ADDRESS,
        to=[recipient],
        cc=[],
        bcc=[],
        subject=f"[RL] run {report.run_id} {report.status}",
        preview=report.model_summary,
        size=len(report.markdown.encode("utf-8")),
    )


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
    all_messages = [_message_summary(report) for report in list_agentmail_reports()]
    return AgentMailMessageList(
        count=len(all_messages),
        messages=all_messages[:limit],
        next_page_token=None,
    )


def get_inbox_message(message_id: str) -> AgentMailMessageDetail:
    prefix = "run:"
    if not message_id.startswith(prefix):
        raise LookupError("AgentMail message not found")

    report = resolve_report(message_id[len(prefix):])
    if report is None:
        raise LookupError("AgentMail message not found")

    summary = _message_summary(report).model_dump(by_alias=True)
    html = _html_report(report)
    return AgentMailMessageDetail.model_validate(
        {
            **summary,
            "text": report.markdown,
            "html": html,
            "extracted_text": report.markdown,
            "extracted_html": html,
            "attachments": [],
            "raw": {
                "run_id": report.run_id,
                "status": report.status,
                "source": _message_source(report),
                "delivery_status": report.delivery_status,
                "external_message_id": report.agentmail_message_id,
                "external_thread_id": report.agentmail_thread_id,
                "artifact_links": report.artifact_links,
            },
        }
    )
