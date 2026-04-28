# Reporting

Reports should be evidence-backed and link back to artifacts.

## When to Send

- benchmark suite completed
- run failed unexpectedly
- reward-hacking flags appeared
- user explicitly asks for a report

## Report Contents

- run ID and env ID
- status and duration
- config summary
- final metrics
- reward-hacking summary
- model/checkpoint path
- W&B URL if present
- GIF/report/log artifact links. Every completed training run should have a default GIF.
- next recommendation

## Channel Split

- AgentMail/Slack: human-readable final report or alert.
- Nia: concise lesson note with artifact locations.
- W&B: charts, curves, and experiment comparison.
- `runs/`: local canonical artifacts.
