# League results audit notes

`results.csv` is append-only as required by the project rules.

The first HTTP batch wrote rows 5–13 using a stale `RandomBot` process that was still bound to port 5009. Those nine rows are mislabeled as `calling_station`, `always_half`, and `always_pot`; disregard them. The corrected full HTTP rerun follows those rows and verified each opponent's `/` endpoint name before playing. The first three rows (`random`, seeds 0–2) were valid.

The first corrected full-zoo league stored `think_s` as the sum across both duplicate halves. In the targeted timing rerun rows later in `results.csv`, `think_s` is the slower half; the run output printed each half separately.

The results after the targeted timing rows include the current 12,000-state test-corpus runs for Methods 2–4 and the earlier fresh-server official HTTP validation for `m1_equity` (four baselines, seeds 7–9). The later rows record candidate comparisons: 10 `equity_pressure` vs `m1_equity` seeds, 10 `equity_guarded` vs `m1_equity` seeds, 12 `equity_guarded` vs starter-baseline matches, and a 200-deal HTTP validation of the 5,000-iteration MCCFR+ policy vs `m1_equity`. A separate 1,000-deal logged replay was generated for the viewer.

Two short development-only protocol-smoke matches (`candidate-smoke` and `replay-demo`, 10 and 3 deals) were removed from the ledger so the committed results contain only meaningful tournament-length comparisons. They had zero errors; the full logged replay is saved under `/tmp/pokerMAKK-guarded-replay/`.

`tools/run_datathon_match.py` appends future fresh-server match summaries automatically. It writes LF-terminated CSV rows so `git diff --check` remains clean.

On 2026-11-07, CSV lines 126–128 record an initial river-bluff-only version of `m5_challenger`; lines 129–158 use the later version that also folds marginal postflop calls. These rows therefore do not describe the same strategy. Lines 129–131 are development seeds, as are the zoo seeds 0–2. Later head-to-head rows use the latter version; seeds 3 and 4 were held out from those initial trials.

M6 development runs are identified by CSV line numbers: 282–284 used loose pressure and baseline calls; 285–287 added tighter calls; 288–290 also reduced thin raises; 291–293 narrowed pressure; 294–296 used 64 postflop samples; 297–299 added a refined preflop table; 300–302 opened a wider button range; 303–305 tested pot-sized pressure; 306–312 used tighter postflop responses with 64 samples. The latter batch was interrupted after the first Method 2 match exceeded the four-second target. Starting at line 313 the candidate uses 48 postflop samples. Seeds 0–2 in these runs were used for development and are not held-out evaluation.

The final M6 candidate's expanded zoo run starts at line 316, followed by the four original methods and a ten-seed M5 batch at lines 373–382. Seeds 0–2 were used for tuning; M5 seeds 3–9 are held out. Lines 383–386 are separate fresh-server HTTP matches against M5, with seeds 11–14. M6's table refines 7,071 near-threshold hands with 250 additional independent simulations per hand, combined with the original 100-sample estimates; other hands retain the original table values.

The strategy recorded as `m6_counter` above was renamed `m5_counterplay` before integration to distinguish it from other M6 work. The rows retain their original labels.

The Bayesian response-EV prototype was screened separately against 19 strategies on three paired seeds × 200 deals each. All 57 matches had zero errors/fallbacks. It averaged +4.070 bb/deal across the pool, driven by large wins over the toy styles, but averaged −1.728 vs `m1_equity`, −2.462 vs `equity_guarded`, and −1.478 vs the newly added `m5_challenger`; therefore it was kept out of the active bot. Per-seed rows are saved in `league/benchmarks/bayes_ev_screen.csv`.

The teammate-added `m5_challenger` was evaluated with fresh servers and the official judge. Seeds 700–709 vs `equity_guarded` produced +0.362 bb/deal over 10,000 paired deals (95% CI [+0.205, +0.518]); all 20 halves had zero errors/timeouts. Seeds 7–9 against each of the four starter baselines produced 12 wins and zero errors/timeouts. These rows are in `results.csv`; this evidence justified making `m5_challenger` the default while preserving the previous policies for comparison.

Counterplay retest: the mainline rows use seeds 0–2 and therefore repeat prior deals. Rows with the `branch_..._ada47a2` prefix use seeds 20–22 against an isolated extraction of `origin/codex/method1` commit `ada47a2`. The `branch_m5_challenger_ada47a2` opponent combines mainline M5 with that branch's Method 1 dependency; it is a simulated integration, not a committed branch bot. The branch's Method 1 estimator and reference/equity policies were loaded separately from the mainline candidate. All these runs append to this ledger.

Counterplay attack research: lines 539–562 record 300-deal `lab_` pressure-raise screens on seeds 31–32; lines 563–592 record the second 300-deal lead/call/opening sweep on those same development seeds. Lines 593–610 are the first full-length implementations; Nightjar, Tidehunter, and Mirrorfin were then tightened, so their current versions begin at lines 611–619. Lines 620–637 are the six final candidates against Counterplay on held-out seeds 40–42. Later `m5_challenger` rows use the upgraded adaptive strategy; the earlier implementation remains available as `m5_classic`. Zoo rows are appended as each parallel process finishes a match; pairs were run concurrently, so timings include contention.

For the final six attack policies, each completed a three-seed, 1,000-deal expanded zoo run; paired processes wrote individual temporary logs and appended every completed match to this ledger. Counterplay holdout seeds 40–42 were not used in the screens or retuning. Fresh-server official judge matches for the upgraded `m5_challenger` against Counterplay use seeds 43–45. The original M5 is preserved as `m5_classic` so older and newer results can be distinguished.

After the full-length evaluations, each of the five new named bots also played a 100-deal fresh-server HTTP protocol check against Counterplay on seed 46. These short matches are interface checks, not evidence comparable to the 1,000-deal evaluations. The upgraded M5's fresh-server 1,000-deal matches use seeds 43–45.
