---
name: apollolabs-curriculum-experimentation
description: Use when launching, monitoring, comparing, diagnosing, visualizing, or reporting Apollo Labs RL curriculum runs
---

# Apollo Labs curriculum experimentation

## Rules

- Use the Apollo Labs MCP for environment and run operations.
- Do not call training scripts directly unless the MCP server is unavailable.
- Start with smoke runs before longer training or benchmark sweeps.
- Use W&B, local metrics, and run artifacts as the source of truth for numbers.
- Expect every completed training run to have a default GIF artifact.
- Use Nia for prior lessons, documents, decisions, and concise run memories.
- Check reward-hacking diagnostics before recommending a winning config.
- Keep Webots work out of this workflow unless the requested env/backend supports it.

## Workflow

1. Search Nia for relevant prior lessons when choosing or tuning a config.
2. Use `list_envs` and `describe_env` if the env choice or defaults are unclear.
3. Launch one smoke run before scaling timesteps, seeds, or variants.
4. Poll `get_run_status` until the run completes or fails.
5. Compare completed runs with `compare_runs`.
6. Inspect reward-hacking output with `summarize_reward_hacking`.
7. Confirm the default GIF exists for completed runs; regenerate only if it is missing or extra episodes are needed.
8. Write a concise Nia note with artifact locations after meaningful runs.
9. Send a report through AgentMail or Slack when requested or after benchmark suites.

## Tool Use

Required Apollo Labs MCP tools:

- `mcp_apollolabs_list_envs`
- `mcp_apollolabs_describe_env`
- `mcp_apollolabs_start_training_run`
- `mcp_apollolabs_get_run_status`
- `mcp_apollolabs_compare_runs`
- `mcp_apollolabs_summarize_reward_hacking`

Regeneration Apollo Labs MCP tools:

- `mcp_apollolabs_start_eval_run`
- `mcp_apollolabs_generate_run_gif`

Use MCP resources for config, metrics, progress, artifacts, trajectory, report, and logs.

## References

- Tool schemas and resource URIs: `references/mcp-tools.md`
- Run config profiles: `references/run-spec.md`
- Ranking and diagnostics: `references/metrics.md`
- Nia memory notes: `references/nia-memory.md`
- AgentMail and Slack reports: `references/reporting.md`
