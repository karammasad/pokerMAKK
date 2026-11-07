# Rules for coding agents in pokerMAKK

- Never edit the SERVER PLUMBING section of agent.py, or game.py, evaluator.py, judge_engine.py,
  docker/, tools/, baseline-bots/.
- agent.py's YOUR CODE HERE section only forwards to bots/active.py. Bot logic lives in bots/.
- Every bot module exposes new_half(config, memory), choose_action(obs, memory) -> Action,
  on_hand_end(result, memory), and is called only through bots/common/safe.py.
- Keep per-half state in `memory`, never in module globals. Write files only under /tmp.
- Every returned action must be in obs.legal_actions.
- Decision time: about 2 ms on average, under 4 s total per half. Check with
  `python league/run.py --timing`.
- Score hands only with evaluator.omaha_score.
- Before calling a task done: `python -m pytest -q` and
  `python league/run.py --bot <name> --zoo all --seeds 3` must pass with 0 errors.
- Append every league run to league/results.csv. Never delete rows.
- Files under 100 MB, no Git LFS.
