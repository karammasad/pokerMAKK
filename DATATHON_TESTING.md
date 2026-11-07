# Testing against the Datathon environment

## 1. Fast local checks

```sh
python3 -m pytest -q
python3 -m compileall -q bots league tests agent.py
```

The default pytest run checks known Short Deck rankings, exact Omaha 2+3-card usage, game-state/chip invariants, deterministic suit symmetry, safety fallbacks, the 5,000-state legal-action fuzz test, and a saved 12,000-observation corpus tested against every strategy. That corpus covers all four streets, both positions, every action set, 648 all-in responses, and 381 states at the four-raise cap. One HTTP parity test is skipped by default.

Rebuild the corpus deterministically with `python3 tests/build_state_corpus.py --states 12000`.

## 2. Real HTTP judge parity

Run the same seed through the real referee and compare it with the direct simulator:

```sh
RUN_HTTP_MATCH_TESTS=1 python3 -m pytest -q tests/test_datathon_http.py
```

This starts the agent and random baseline on temporary local ports, has `judge_engine.py` play both halves, and asserts its per-deal paired chip results exactly match the in-process league.

## 3. Tournament-style fresh-server matches

The tournament starts a new server for each half. Use the helper below; it launches both servers fresh for half 1, stops them, starts fresh servers for half 2, then combines the halves with the official judge:

```sh
python3 tools/run_datathon_match.py --opponent baseline_random --seed 7 --deals 1000
```

For all four starter baselines and three consecutive seeds:

```sh
python3 tools/run_datathon_match.py --opponent all --seed 7 --seeds 3 --deals 1000
```

It saves each half and the combined judge result under `/tmp/pokerMAKK-datathon/` and appends a summary row to `league/results.csv`. Use a different `--outdir` if you need to preserve prior run files.

The current default, `equity_guarded`, won all 12 fresh-server matches against the four starter baselines (seeds 7–9, 1,000 deals each), with zero errors. The slowest thinking half was 0.77 seconds.

## 4. Compare our research-inspired candidates

The local league can screen the five equity portfolio candidates against all nine practice styles and one another:

```sh
python3 league/run.py --bot equity_precise --opp all --seeds 3 --deals 200 --out /tmp/equity-precise-screen.csv
```

Candidate names are `equity_core`, `equity_guarded`, `equity_pressure`, `equity_precise`, and `bayes_adaptive`. Use the same seed range for every candidate, then confirm leaders with the official HTTP judge. For example:

```sh
python3 tools/run_datathon_match.py --bot equity_guarded --opponent-bot m1_equity --seed 711 --seeds 10 --deals 1000
```

These are research-inspired policy variants around our tested equity engine, not full reproductions of DeepStack or Libratus. The original `m2_cfr` remains a coarse one-street warm-start scaffold.

The repo also includes an external-sampling MCCFR+ trainer over the official sequential betting game. It uses an explicit imperfect-recall information-state abstraction, so full-game convergence guarantees do not transfer directly to this prototype. The checked-in 5,000-iteration policy currently loses to the equity baseline; train a candidate, then compare it on held-out seeds before adoption:

```sh
python3 -m bots.mccfr.train.solver --iterations 5000 --seed train-v1 --out bots/mccfr/tables/strategy.json
python3 tools/run_datathon_match.py --bot mccfr --opponent-bot equity_guarded --seed 700 --seeds 10 --deals 1000
```

## 5. Test a shared/organizer bot

The participant guide describes a round-robin tournament but does not publish other teams' bot code or an opponent endpoint. Ask the organizers whether they can provide a sample opponent package or a local runnable bot; teams can also share a copy of their entry. The other bot must be run with the same protocol/dependencies as this bundle. Do not assume a live tournament endpoint is available: tournament containers have no outside network access.

If you receive a compatible Python server script, run it as a second process for each half with:

```sh
python3 tools/run_datathon_match.py \
  --opponent-script /absolute/path/to/other_team/agent.py \
  --opponent-name OtherTeamBot \
  --seed 7 --seeds 10 --deals 1000
```

`--opponent-name` must match the opponent's `GET /` JSON `agent_name`. The runner launches fresh processes for each half, uses the official local judge on identical duplicate deals, combines the halves, and records the results. `--seeds 10` gives ten reproducible paired matches; each match uses the same seed for both seats. If the bot needs extra packages, install them in the active Python environment first. For a Docker-only bot, start its HTTP server on the assigned `PORT` yourself and use the judge directly (`python3 judge_engine.py --half 1 --agent1 5008 --agent2 5011 --seed 7 --deals 1000`), then restart both servers and repeat with `--half 2`; combine the JSON files with `python3 judge_engine.py combine half1.json half2.json`.

Start with 100–200 deals to catch protocol, import, and illegal-action problems. Then use at least 10 seeds at the full 1,000 deals per half and compare mean bb/deal, confidence intervals, forfeits, errors, and time bank. Keep actual submitted bots in a separate result group from the four toy baselines.

## 6. Watch a match

Add `--logs` to a fresh-server run and open the combined JSON in the standalone replay viewer:

```sh
python3 tools/run_datathon_match.py --bot equity_guarded --opponent-bot m1_equity --seed 711 --deals 1000 --logs
python3 tools/view_match.py /tmp/pokerMAKK-datathon/m1_equity-seed-711/match.json --open
```

The viewer lets you step through hands and inspect the board, both hands, button, actions, pot, and per-hand chip result. Logs reveal private cards after the hand, so only use saved results from matches whose hands you are allowed to review.

## 7. Build and submission checks

```sh
./tools/check_build.sh
```

This is the same Docker build and restricted-container smoke check used by the starter. Before submitting, confirm the repo is public, the tested commit SHA is pushed, and the build succeeds. A local HTTP win is not a replacement for the Docker/runtime check.

## What a match result means

A single half is mostly card luck. The judge keeps the same deals and swaps seats for the second half, then reports the mean big blinds per deal and a 95% confidence interval. Above zero is a win, below zero is a loss, and an interval touching zero is a chop. A five-error half is a forfeit. Track errors, timeouts, and decision time along with chip results.
