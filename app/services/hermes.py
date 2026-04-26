import json
import time
from dataclasses import dataclass
from typing import Optional
from urllib import error, parse, request

from app import config
from app.schemas.run import RunReport
from app.services.agentmail import AgentMailResult, send_report

HERMES_REPORT_RECIPIENTS: list[str] = (
    list(config.REPORT_RECIPIENT_EMAILS) if config.REPORT_RECIPIENT_EMAILS else ["nikhilprabhu06@gmail.com"]
)
HERMES_REPORT_RECIPIENT = ", ".join(HERMES_REPORT_RECIPIENTS)


@dataclass
class HermesPostResult:
    status: str  # "posted" | "skipped" | "failed"
    error: Optional[str] = None
    agentmail: Optional[AgentMailResult] = None


# ---------------------------------------------------------------------------
# Slack helpers
# ---------------------------------------------------------------------------

def _slack_post(url: str, body: dict, token: Optional[str] = None) -> dict:
    payload = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Slack HTTP {exc.code}: {detail}") from exc


def _slack_get(url: str, params: dict) -> dict:
    qs = parse.urlencode(params)
    req = request.Request(
        f"{url}?{qs}",
        headers={"Authorization": f"Bearer {config.SLACK_BOT_TOKEN}"},
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(str(exc)) from exc


def _post_message(text: str, blocks: Optional[list] = None) -> Optional[str]:
    """Post via chat.postMessage, return message ts."""
    body: dict = {"channel": config.SLACK_CHANNEL_ID, "text": text}
    if blocks:
        body["blocks"] = blocks
    try:
        data = _slack_post(
            "https://slack.com/api/chat.postMessage", body, token=config.SLACK_BOT_TOKEN
        )
        if data.get("ok"):
            return data.get("ts")
        return None
    except Exception:
        return None


def _get_replies(thread_ts: str) -> list[str]:
    """Return text of all replies in a thread (excludes the root message)."""
    try:
        data = _slack_get(
            "https://slack.com/api/conversations.replies",
            {"channel": config.SLACK_CHANNEL_ID, "ts": thread_ts},
        )
    except Exception:
        return []
    messages = data.get("messages") or []
    return [m["text"] for m in messages[1:] if m.get("text")]


# ---------------------------------------------------------------------------
# Before-run: query Nia via Hermes
# ---------------------------------------------------------------------------

def query_nia(template: str, run_config: dict) -> str:
    """
    Post a pre-run query to Hermes in Slack. Hermes searches Nia and replies.
    Returns Hermes' reply text, or "" if unavailable/timeout.
    """
    if not config.SLACK_BOT_TOKEN or not config.SLACK_CHANNEL_ID:
        return ""

    config_summary = ", ".join(
        f"{k}={v}"
        for k, v in run_config.items()
        if k in ("room_size", "dirt_count", "total_timesteps", "max_steps", "obstacle_count")
    )

    text = (
        f"[ClawLab] Planning a new training run.\n"
        f"*env_id:* `{template}`\n"
        f"*Config:* {config_summary}\n"
        f"Please search Nia for relevant prior lessons on this environment "
        f"and reply with what worked, what failed, and any recommendations."
    )

    ts = _post_message(text)
    if not ts:
        return ""

    for _ in range(6):  # poll up to 30s
        time.sleep(5)
        replies = _get_replies(ts)
        if replies:
            return "\n".join(replies)

    return ""


# ---------------------------------------------------------------------------
# After-run: post lesson note
# ---------------------------------------------------------------------------

def _status_emoji(status: str) -> str:
    return {"success": "✅", "completed": "✅", "failed": "❌", "early_stop": "⏹"}.get(status, "🔵")


def _derive_lesson(report: RunReport) -> tuple[str, str, str]:
    sr = report.best_return or 0.0
    mr = report.mean_return or 0.0

    if report.status == "failed" and report.error:
        return (
            "n/a — run did not complete",
            f"Run error: {report.error}",
            "Fix the run error before retrying. Check logs in runs/ directory.",
        )
    if sr >= 0.8:
        return (
            f"Policy converged well. Success rate {sr:.0%}, mean reward {mr:.3f}.",
            "No critical failures.",
            "Config is solid — consider increasing difficulty (larger room or more dirt).",
        )
    if sr >= 0.5:
        return (
            f"Policy showed learning. Success rate {sr:.0%}, mean reward {mr:.3f}.",
            "Policy did not fully converge.",
            "Try increasing total_timesteps by 50% or tuning reward weights.",
        )
    return (
        f"Minimal learning signal. Mean reward {mr:.3f}.",
        f"Low success rate ({sr:.0%}). Policy struggled with this config.",
        "Increase timesteps significantly, simplify env (smaller room/fewer dirt), or revisit reward shaping.",
    )


def send_run_email(report: RunReport) -> AgentMailResult:
    """Hermes sends the end-of-run AgentMail report to the configured recipients."""
    return send_report(report, recipient=HERMES_REPORT_RECIPIENTS)


def post_lesson(report: RunReport) -> HermesPostResult:
    """
    Post a structured run lesson note to Hermes in Slack and email the run report
    via AgentMail (Hermes is the agent that triggers the email).
    Uses webhook if no bot token; bot token preferred for consistency.
    """
    mail_result = send_run_email(report)
    recipient_label = ", ".join(HERMES_REPORT_RECIPIENTS) or HERMES_REPORT_RECIPIENT
    report.agentmail_message_id = mail_result.message_id
    report.agentmail_thread_id = mail_result.thread_id
    report.delivery_status = mail_result.delivery_status
    report.delivery_error = mail_result.error

    if not config.SLACK_WEBHOOK_URL and not config.SLACK_BOT_TOKEN:
        return HermesPostResult(status="skipped", agentmail=mail_result)

    what_worked, what_failed, next_rec = _derive_lesson(report)
    emoji = _status_emoji(report.status)
    cfg = report.config or {}
    config_summary = ", ".join(
        f"{k}={v}"
        for k, v in cfg.items()
        if k in ("room_size", "dirt_count", "total_timesteps", "max_steps")
    )

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"[ClawLab Note] {emoji} Run `{report.run_id}`"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*env_id*\n`{report.template}`"},
                {"type": "mrkdwn", "text": f"*result*\n{report.status} | reward {report.mean_return:.3f} | policy success {report.best_return:.0%}"}
                if report.mean_return is not None and report.best_return is not None
                else {"type": "mrkdwn", "text": f"*result*\n{report.status}"},
            ],
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Config*\n{config_summary}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*What worked*\n{what_worked}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*What failed*\n{what_failed}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*Next recommendation*\n{next_rec}"}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*Report email*\n{mail_result.delivery_status} → `{recipient_label}`"
                    + (f" — {mail_result.error}" if mail_result.error else "")
                ),
            },
        },
    ]

    if report.error:
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*Error*\n```{report.error}```"}}
        )

    base_url = (config.HERMES_PUBLIC_BASE_URL or "").rstrip("/")
    if base_url and report.run_id:
        dashboard_url = f"{base_url}/runs/{report.run_id}"
    else:
        dashboard_url = (report.artifact_links or {}).get("dashboard", "") or base_url
    if dashboard_url:
        blocks.append({
            "type": "actions",
            "elements": [{"type": "button", "text": {"type": "plain_text", "text": "View Dashboard →"}, "url": dashboard_url}],
        })

    # Prefer bot token (chat.postMessage); fall back to webhook
    if config.SLACK_BOT_TOKEN and config.SLACK_CHANNEL_ID:
        fallback = f"[ClawLab Note] {report.run_id} {report.status}"
        ts = _post_message(fallback, blocks=blocks)
        if ts is not None:
            return HermesPostResult(status="posted", agentmail=mail_result)
        return HermesPostResult(status="failed", error="chat.postMessage returned no ts", agentmail=mail_result)

    # Webhook fallback
    payload = json.dumps({"blocks": blocks}).encode("utf-8")
    req = request.Request(
        config.SLACK_WEBHOOK_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        return HermesPostResult(status="failed", error=f"HTTP {exc.code}", agentmail=mail_result)
    except Exception as exc:
        return HermesPostResult(status="failed", error=str(exc), agentmail=mail_result)

    if body.strip() == "ok":
        return HermesPostResult(status="posted", agentmail=mail_result)
    return HermesPostResult(status="failed", error=body, agentmail=mail_result)
