from pathlib import Path
import os

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

RUNS_DIR = PROJECT_ROOT / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

AGENTMAIL_API_KEY = os.getenv("AGENTMAIL_API_KEY", "")
AGENTMAIL_INBOX_ID = os.getenv("AGENTMAIL_INBOX_ID", "")
AGENTMAIL_API_BASE_URL = os.getenv("AGENTMAIL_API_BASE_URL", "https://api.agentmail.to/v0")
REPORT_RECIPIENT_EMAIL = os.getenv("REPORT_RECIPIENT_EMAIL", "")
HERMES_PUBLIC_BASE_URL = os.getenv("HERMES_PUBLIC_BASE_URL", "http://localhost:3000")
SLACK_HERMES_CHANNEL = os.getenv("SLACK_HERMES_CHANNEL", "#hermes-agent")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
