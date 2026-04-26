# ClawLab MCP Tools

Configure Hermes with server name `clawlab` so discovered tools use the `mcp_clawlab_*` prefix.

```yaml
mcp_servers:
  clawlab:
    command: "/Users/adavya/Downloads/openclaw-hackathon/.venv/bin/python"
    args: ["-m", "app.mcp.clawlab_server"]
    cwd: "/Users/adavya/Downloads/openclaw-hackathon"
```

## Tools

`list_envs()`
Returns registered curriculum envs, default kwargs, reward components, and metric fields.

`describe_env(env_id: str)`
Returns one env spec. Use before generating a config for an unfamiliar env.

`start_training_run(config: dict)`
Starts a validated PPO run. Include `env_id`, timesteps, eval episodes, seed, sensor settings, and device. Completed runs should include a default GIF and trajectory in artifacts.

`get_run_status(run_id: str)`
Polls run metadata, artifact availability, and resource URIs.

`start_eval_run(run_id: str, episodes: int = 20)`
Runs evaluation for an existing trained run and writes eval metrics.

`compare_runs(run_ids: list[str])`
Ranks runs by success, reward-hacking flags, remaining dirt, collisions, and reward.

`generate_run_gif(run_id: str, episodes: int = 1)`
Regenerates rollout GIF and trajectory artifacts or adds extra visual episodes. Use when the default GIF is missing or more visual evidence is needed.

`summarize_reward_hacking(run_id: str)`
Reads reward-hacking diagnostics and returns a concise interpretation.

## Resources

- `clawlab://envs`
- `clawlab://runs/{run_id}/metadata`
- `clawlab://runs/{run_id}/config`
- `clawlab://runs/{run_id}/metrics`
- `clawlab://runs/{run_id}/progress`
- `clawlab://runs/{run_id}/artifacts`
- `clawlab://runs/{run_id}/trajectory`
- `clawlab://runs/{run_id}/report`
- `clawlab://runs/{run_id}/logs`

Use resources for inspection. Use tools for actions.
