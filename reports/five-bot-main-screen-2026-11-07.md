# Five-bot roster screen and Telltide holdout — 2026-11-07

## What was tested

All five bots ran against all 60 registered `--zoo all` opponents (9 CPU policies, 9 equity policies, and 42 bot-roster entries, including self-play). Every matchup used 200 deals on seed 0. The screen produced 300 rows; each bot has 59 non-self matchups. The earlier 1,000-deal Rangeglass sweep was interrupted during its roster pass, and those partial rows are retained in the append-only ledger but excluded here.

The 200-deal screen is for triage, not a final leaderboard. It uses one seed. Per-match confidence intervals are over the 200 deals; use new paired seeds to confirm close results. Summary averages weight each opponent equally.

## Screen summary

| Bot | Mean bb/deal vs 59 opponents | Wins / losses / chops | Errors / fallbacks | Max half think | Mean p50 decision |
|---|---:|---:|---:|---:|---:|
| telltide | +1.741 | 43 / 0 / 16 | 0 / 0 | 0.648s | 0.777ms |
| riverloom | +1.388 | 23 / 11 / 25 | 0 / 0 | 1.354s | 0.524ms |
| suitspark | +1.280 | 20 / 10 / 29 | 0 / 0 | 1.171s | 1.669ms |
| rangeglass | +1.068 | 14 / 9 / 36 | 0 / 0 | 0.421s | 0.430ms |
| pebble_cfr | -0.742 | 7 / 12 / 40 | 0 / 0 | 0.479s | 0.269ms |

## Telltide holdout: 1,000 deals × 3 new seeds

After Telltide led the screen, it faced 16 priority opponents on seeds 2000–2002. This is a separate confirmation set, not part of the 200-deal ranking. Positive results against M7 Cherki and M5 Classic repeated on all three seeds. Results against the pressure fleet and M5 Challenger stayed close to even or modestly negative.

| Opponent | Mean bb/deal | Seed 2000 | Seed 2001 | Seed 2002 |
|---|---:|---:|---:|---:|
| m5_challenger | -0.110 | -0.351 | +0.020 | +0.001 |
| m5_counterplay | +0.178 | +0.175 | +0.194 | +0.164 |
| turnblade | -0.266 | -0.366 | -0.204 | -0.229 |
| duskfox | -0.070 | -0.186 | +0.058 | -0.081 |
| nightjar | -0.268 | -0.470 | -0.092 | -0.243 |
| tidehunter | -0.214 | -0.363 | -0.083 | -0.197 |
| mirrorfin | -0.289 | -0.385 | -0.145 | -0.338 |
| m7_cherki | +0.865 | +0.806 | +0.664 | +1.126 |
| de_bruyne | +0.142 | +0.402 | +0.266 | -0.243 |
| kestrel | -0.113 | -0.325 | +0.068 | -0.082 |
| rangeglass | -0.032 | -0.088 | +0.111 | -0.119 |
| riverloom | +0.244 | +0.397 | +0.214 | +0.121 |
| suitspark | +0.212 | +0.280 | +0.238 | +0.118 |
| pebble_cfr | +0.475 | +1.075 | +0.334 | +0.016 |
| m5_classic | +0.999 | +1.295 | +0.589 | +1.112 |
| rook_fast | +0.244 | +0.197 | +0.157 | +0.378 |

## Takeaways

- **Telltide is the best candidate to optimize first, but it is not proven best overall.** Its all-roster screen led at +1.741 bb/deal (43 wins, 0 losses, 16 chops), but the one-seed results were noisy. In the larger holdout it beat M7 Cherki by +0.865 bb/deal and M5 Classic by +0.999, with positive results on all three seeds. It was approximately even against M5 Challenger (−0.110 pooled mean) and M5 Counterplay (+0.178).
- **Pressure defense is the clearest shared weakness.** In the 200-deal screen, Rangeglass, Riverloom, and Suitspark lost to M5 Challenger by −0.635, −0.410, and −0.590 bb/deal respectively. They also lost to multiple turn/river pressure bots. PebbleCFR lost by −1.845 to M5 Challenger and −2.583 to M5 Classic.
- **PebbleCFR needs a stronger training policy before strategy tuning.** It averaged −0.742 bb/deal over the screen and lost to many established roster bots; the current small MCCFR+ table is a useful prototype, not a contender.
- **Reliability and speed were good in these runs.** All 300 screen rows and 48 Telltide holdout rows recorded zero errors and zero fallbacks. Maximum half thinking time was 1.354 seconds in the screen and 2.528 seconds in the holdout, both below the 4-second budget.

## Recommended next iteration

Work on Telltide only. Its holdout losses concentrate against Turnblade (−0.266 mean), Nightjar (−0.268), Tidehunter (−0.214), Mirrorfin (−0.289), and M5 Challenger (−0.110). Telltide currently delegates decisions while facing a bet to M5 Counterplay, so the narrow hypothesis is to improve its facing-pressure response using observed opponent action tendencies, while retaining the current M5 fallback. Change one parameter or rule, then compare baseline and variant on identical seeds and keep a separate holdout. Do not tune against the weak CPU opponents.

## Reproducibility

- Full screen: `python3 league/run.py --bot <name> --zoo all --deals 200 --seeds 1` for each of the five names.
- Telltide holdout: `python3 league/run.py --bot telltide --opp m5_challenger,m5_counterplay,turnblade,duskfox,nightjar,tidehunter,mirrorfin,m7_cherki,de_bruyne,kestrel,rangeglass,riverloom,suitspark,pebble_cfr,m5_classic,rook_fast --deals 1000 --seeds 3 --seed-start 2000`.
- Raw append-only ledger: `league/results.csv`.
- Screen rows: `league/benchmarks/five_bot_main_screen_2026-11-07.csv`.
- Holdout rows: `league/benchmarks/telltide_holdout_2026-11-07.csv`.
