# League results audit notes

`results.csv` is append-only as required by the project rules.

The first HTTP batch wrote rows 5–13 using a stale `RandomBot` process that was still bound to port 5009. Those nine rows are mislabeled as `calling_station`, `always_half`, and `always_pot`; disregard them. The corrected full HTTP rerun follows those rows and verified each opponent's `/` endpoint name before playing. The first three rows (`random`, seeds 0–2) were valid.

The first corrected full-zoo league stored `think_s` as the sum across both duplicate halves. In the targeted timing rerun rows later in `results.csv`, `think_s` is the slower half; the run output printed each half separately.

The results after the targeted timing rows include the current 12,000-state test-corpus runs for Methods 2–4 and the earlier fresh-server official HTTP validation for `m1_equity` (four baselines, seeds 7–9). The later rows record candidate comparisons: 10 `equity_pressure` vs `m1_equity` seeds, 10 `equity_guarded` vs `m1_equity` seeds, 12 `equity_guarded` vs starter-baseline matches, and a 200-deal HTTP validation of the 5,000-iteration MCCFR+ policy vs `m1_equity`. A separate 1,000-deal logged replay was generated for the viewer.

Two short development-only protocol-smoke matches (`candidate-smoke` and `replay-demo`, 10 and 3 deals) were removed from the ledger so the committed results contain only meaningful tournament-length comparisons. They had zero errors; the full logged replay is saved under `/tmp/pokerMAKK-guarded-replay/`.

`tools/run_datathon_match.py` appends future fresh-server match summaries automatically. It writes LF-terminated CSV rows so `git diff --check` remains clean.

On 2026-11-07, CSV lines 126–128 record an initial river-bluff-only version of `m5_challenger`; lines 129–158 use the later version that also folds marginal postflop calls. These rows therefore do not describe the same strategy. Lines 129–131 are development seeds, as are the zoo seeds 0–2. Later head-to-head rows use the latter version; seeds 3 and 4 were held out from those initial trials.

The Bayesian response-EV prototype was screened separately against 19 strategies on three paired seeds × 200 deals each. All 57 matches had zero errors/fallbacks. It averaged +4.070 bb/deal across the pool, driven by large wins over the toy styles, but averaged −1.728 vs `m1_equity`, −2.462 vs `equity_guarded`, and −1.478 vs the newly added `m5_challenger`; therefore it was kept out of the active bot. Per-seed rows are saved in `league/benchmarks/bayes_ev_screen.csv`.

The teammate-added `m5_challenger` was evaluated with fresh servers and the official judge. Seeds 700–709 vs `equity_guarded` produced +0.362 bb/deal over 10,000 paired deals (95% CI [+0.205, +0.518]); all 20 halves had zero errors/timeouts. Seeds 7–9 against each of the four starter baselines produced 12 wins and zero errors/timeouts. These rows are in `results.csv`; this evidence justified making `m5_challenger` the default while preserving the previous policies for comparison.
