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

The latest fresh-server validation (seed 7–9, 1,000 deals each) won all 12 matches against the four starter baselines with zero errors. The slowest thinking half was 1.25 seconds.

The helper accepts `baseline_random`, `baseline_calling_station`, `baseline_always_half`, and `baseline_always_pot`. Run other submitted bots as HTTP servers and point `judge_engine.py` at their ports, or add them to the helper's allowlist.

## 4. Build and submission checks

```sh
./tools/check_build.sh
```

This is the same Docker build and restricted-container smoke check used by the starter. Before submitting, confirm the repo is public, the tested commit SHA is pushed, and the build succeeds. A local HTTP win is not a replacement for the Docker/runtime check.

## What a match result means

A single half is mostly card luck. The judge keeps the same deals and swaps seats for the second half, then reports the mean big blinds per deal and a 95% confidence interval. Above zero is a win, below zero is a loss, and an interval touching zero is a chop. A five-error half is a forfeit. Track errors, timeouts, and decision time along with chip results.
