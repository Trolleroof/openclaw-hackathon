import json
from dataclasses import dataclass
from typing import Optional
from urllib import error, request

from app import config
from app.schemas.run import RunReport


@dataclass
class HermesPostResult:
    status: str  # "posted" | "skipped" | "failed"
    error: Optional[str] = None


def _status_emoji(status: str) -> str:
    return {"success": "✅", "completed": "✅", "failed": "❌", "early_stop": "⏹"}.get(status, "🔵")


def _fmt(value: Optional[float], decimals: int = 3) -> str:
    return f"{value:.{decimals}f}" if value is not None else "n/a"


def _build_lesson_blocks(report: RunReport) -> list:
    emoji = _status_emoji(report.status)
    header_text = f"[ClawLab Lesson] Run `{report.run_id}` — {emoji} {report.status}"

    fields = [
        {"type": "mrkdwn", "text": f"*Template*\n`{report.template}`"},
        {"type": "mrkdwn", "text": f"*Algo*\nPPO"},
        {"type": "mrkdwn", "text": f"*Timesteps*\n{report.steps or 0:,}"},
        {"type": "mrkdwn", "text": f"*Duration*\n{report.duration_sec:.1f}s" if report.duration_sec else "*Duration*\nn/a"},
        {"type": "mrkdwn", "text": f"*Mean reward*\n{_fmt(report.mean_return)}"},
        {"type": "mrkdwn", "text": f"*Success rate*\n{_fmt(report.best_return)}"},
    ]

    cfg = report.config or {}
    config_text = " | ".join(f"{k}={v}" for k, v in [
        ("room_size", cfg.get("room_size")),
        ("dirt_count", cfg.get("dirt_count")),
        ("max_steps", cfg.get("max_steps")),
        ("seed", cfg.get("seed")),
    ] if v is not None)

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": header_text}},
        {"type": "section", "fields": fields},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*What happened*\n{report.model_summary}"}},
    ]

    if report.error:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Failure*\n```{report.error}```"},
        })

    if config_text:
        blocks.append({
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"Config: {config_text}"}],
        })

    dashboard_url = (report.artifact_links or {}).get("dashboard", "")
    if dashboard_url:
        blocks.append({
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "View Dashboard →"},
                "url": dashboard_url,
            }],
        })

    return blocks


def post_lesson(report: RunReport) -> HermesPostResult:
    """Post a structured run lesson to the Hermes Slack channel via Incoming Webhook."""
    if not config.SLACK_WEBHOOK_URL:
        return HermesPostResult(status="skipped")

    blocks = _build_lesson_blocks(report)
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
        detail = exc.read().decode("utf-8", errors="replace")
        return HermesPostResult(status="failed", error=f"HTTP {exc.code}: {detail}")
    except Exception as exc:
        return HermesPostResult(status="failed", error=str(exc))

    if body.strip() == "ok":
        return HermesPostResult(status="posted")
    return HermesPostResult(status="failed", error=body)
