# OpenClaw Robot — Webots MVP

Chat command → diff-drive robot moves in Webots sim, live on your M4 Mac.

## How it works

```
You type in OpenClaw
       │
       ▼
 robot_skill.py   (Python + Webots' bundled `controller` API)
       │
       │  TCP localhost   (Webots extern controller protocol)
       ▼
 Webots GUI        ← you watch the robot move here
 robot_world.wbt
```

No ROS. No bridge. No compile step.

## Setup (one-time, ~5 minutes)

### 1. Install Webots

Download the native macOS `.dmg` from https://cyberbotics.com and drag to
`/Applications`. That's it — it runs natively on Apple Silicon M-series chips.

### 2. Optional: project virtualenv (recommended on Homebrew Python)

Homebrew marks the system Python as “externally managed” (PEP 668), so use a venv for any extra packages:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r openclaw/requirements.txt   # file is comment-only; controller comes from Webots
```

The Webots `controller` module is **not** on PyPI — it ships inside the Webots app. `scripts/run_skill.sh` sets `PYTHONPATH` (and `DYLD_LIBRARY_PATH` on macOS) for you.

### 3. Tell tools where Webots lives

```bash
export WEBOTS_HOME=/Applications/Webots.app
# Add to ~/.zshrc to make it permanent
```

## Running the demo

### Step 1 — open the world in Webots

```
File → Open World → webots_project/worlds/robot_world.wbt
```

You'll see a blue diff-drive robot in an arena. The sim is paused waiting for
an external controller to connect.

### Step 2 — run the skill

```bash
# From the repo root, two options:

# Option A — shell helper
./scripts/run_skill.sh "move forward 2 seconds"

# Option B — direct Python (same thing)
python openclaw/robot_skill.py "move forward 2 seconds"
```

The robot moves in the Webots window. The script exits when the movement
finishes. Run it again with any command.

### Supported commands

| Phrase | Action |
|--------|--------|
| `move forward [N seconds \| N meters]` | Drive straight |
| `go backward / reverse [N seconds]` | Drive in reverse |
| `turn left [N seconds]` | Pivot left |
| `turn right [N seconds]` | Pivot right |
| `spin [N seconds]` | Spin in place |
| `stop / halt` | Immediate stop |

Examples:

```bash
python openclaw/robot_skill.py "move forward 1 meter"
python openclaw/robot_skill.py "turn left 3 seconds"
python openclaw/robot_skill.py "go backward 2 seconds"
python openclaw/robot_skill.py "spin"
python openclaw/robot_skill.py "stop"
```

## Using from OpenClaw

Register `openclaw/robot_skill.py::move_robot` as a skill. It takes a single
`command` string and returns a confirmation:

```python
from robot_skill import move_robot

move_robot("move forward 2 seconds")   # → "Moved forward ~0.60 m (2.0s)."
move_robot("turn left 3 seconds")      # → "Turned left for 3.0s."
```

## Tuning

Edit the constants at the top of `openclaw/robot_skill.py`:

```python
WHEEL_SPEED  = 6.0   # rad/s  — increase for faster robot
TURN_SPEED   = 4.0   # rad/s  — increase for faster turns
WHEEL_RADIUS = 0.05  # metres — must match robot_world.wbt
DEFAULT_SECS = 2.0   # fallback when no duration is given
```

## File layout

```
webots_project/
  worlds/
    robot_world.wbt     ← open this in Webots
openclaw/
  robot_skill.py        ← OpenClaw skill / standalone CLI
  requirements.txt
scripts/
  run_skill.sh          ← convenience wrapper
```

## Ideas: [AgentMail](https://docs.agentmail.to/welcome)

[AgentMail](https://docs.agentmail.to/introduction) is an API for **dedicated agent inboxes**—send, receive, and act on email as structured messages and threads, with webhooks or WebSockets for inbound mail, drafts for review before send, and pods for multi-tenant isolation. Docs: [llms index](https://docs.agentmail.to/llms.txt), [OpenClaw integration](https://docs.agentmail.to/integrations/openclaw), [MCP](https://docs.agentmail.to/integrations/mcp).
