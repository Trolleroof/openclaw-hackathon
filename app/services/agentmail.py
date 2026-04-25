import json
from dataclasses import dataclass
from typing import Optional
from urllib import error, request

from app import config
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


def send_report(report: RunReport) -> AgentMailResult:
    if not config.AGENTMAIL_API_KEY or not config.AGENTMAIL_INBOX_ID or not config.REPORT_RECIPIENT_EMAIL:
        return AgentMailResult(delivery_status="skipped", error="AgentMail is not configured")

    body = {
        "to": [config.REPORT_RECIPIENT_EMAIL],
        "subject": f"[RL] run {report.run_id} {report.status}",
        "text": report.markdown,
        "html": _html_report(report),
        "labels": ["hermes", "run-report", report.status],
    }
    url = f"{config.AGENTMAIL_API_BASE_URL.rstrip('/')}/inboxes/{config.AGENTMAIL_INBOX_ID}/messages"
    payload = json.dumps(body).encode("utf-8")
    req = request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {config.AGENTMAIL_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8") or "{}")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return AgentMailResult(delivery_status="failed", error=f"AgentMail HTTP {exc.code}: {detail}")
    except Exception as exc:
        return AgentMailResult(delivery_status="failed", error=str(exc))

    return AgentMailResult(
        delivery_status="sent",
        message_id=data.get("id") or data.get("message_id"),
        thread_id=data.get("thread_id") or data.get("threadId"),
    )
