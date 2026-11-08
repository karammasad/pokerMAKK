# Poker bot catalog

These are human-readable labels for discussion. The **runnable ID** remains the exact module or portfolio name used by `POKER_BOT`, the league runner, and historical CSV rows. A label does not imply that a bot is the strongest. Select an entry with `POKER_BOT=<runnable ID>` or `league/run.py --bot <runnable ID>`.

| Label | Runnable ID | Description | Status |
| --- | --- | --- | --- |
| Anchor | `m5_challenger` | Adaptive turn pressure over the counterplay equity policy | Current entry default |
| Talon | `m5_counterplay` | Refined preflop table and pressure-oriented postflop policy | Team comparison candidate |
| M5 Classic | `m5_classic` | Preserved original M5; anchor for existing teammate strategies | Historical reference |
| Turnblade | `turnblade` | Fixed turn pressure | Counterplay challenger |
| Duskfox | `duskfox` | Turn and river pressure | Counterplay challenger |
| Nightjar | `nightjar` | Turn pressure with mixed flop and river bluffs | Counterplay challenger |
| Tidehunter | `tidehunter` | Turn pressure plus mixed button opens | Counterplay challenger |
| Mirrorfin | `mirrorfin` | Turn pressure plus selective river calls | Counterplay challenger |
| Rook | `m11_chosen` | Anchor preflop and Talon postflop | Comparison candidate |
| Rangefinder | `rangefinder` | M5-derived policy with confidence-shrunk showdown range updates | Research challenger |
| Lens | `m7_precision` | Anchor with selective extra equity sampling | Comparison candidate |
| Guard | `equity_guarded` | Guarded equity portfolio policy | Comparison candidate |
| Scout | `m1_equity` | Original equity policy | Baseline |
| Shield | `m6_safeadapt` | Anchor with bounded response-based adjustments | Research comparator |
| Profiles | `m8_bayes_types` | Public-action type posterior | Research comparator |
| Regret | `m9_cfrplus` | Compact MCCFR+ table with fallback | Research comparator |
| Sequence | `m10_seq_cfr` | Sequence-aware MCCFR+ table with fallback | Research comparator |
| Gundogan | `gundogan` | Captain: precision pressure, gated turn/river attacks, call-down vs aggressors, M5 style only vs true maniacs | City family candidate |
| Akanji | `akanji` | Precision pressure with call-down vs all aggressors | City family candidate |
| Doku | `doku` | All teammate attacks (turn/river/flop-mix, mixed opens, river calls) over the City engine | City family candidate |
| Stones | `stones` | Disciplined gated turn pressure plus river calls | City family candidate |
| Ederson | `ederson` | Adaptive exploiter: bluffs folders, thins value vs stations | City family candidate |
| Mahrez | `mahrez` | Ballsy v2: overbluffs, floats, bluff-raises plus gated pressure, -80bb stop-loss | City family candidate (exploitable by turn-pressure bots) |
| Haaland / De Bruyne / Rodri / Foden / Bernardo / Grealish | `haaland`, `de_bruyne`, `rodri`, `foden`, `bernardo`, `grealish` | First City family (shared `bots/city_core.py`); `grealish` is the ballsy one | City family comparison candidates |
| Cherki | `m7_cherki` | Counterplay core + near-threshold precision + M5-classic switch vs aggression | Comparison candidate |
| Methods 2–4 | `m2_cfr`, `m3_exploit`, `m4_learned` | Earlier experimental policies | Research comparators |
| MCCFR | `mccfr` | Earlier sequential MCCFR prototype | Research comparator |
| Cherki | `m7_cherki` | Teammate's adaptive pressure policy | Comparison candidate |
| Hawk | `m1_team_tuned` | Teammate's tuned Method 1 snapshot from branch `codex/method1` | Evaluation candidate |
| Swift Rook | `rook_fast` | Rook with identical-equity river optimization and per-hand caching | Evaluation candidate |
| Frozen Scout | `m1_reference` | Teammate's frozen Method 1 control | Research comparator |
| Kestrel | `kestrel` | Talon with the evidence-gated semi-bluff extended from turn-only to turn and river | Research candidate, not promoted |
| Equity sparring | `equity_balanced`, `equity_tight`, `equity_loose` | Teammate's frozen-equity threshold variants | In-process sparring opponents |
| Portfolio | `equity_core`, `equity_pressure`, `equity_precise`, `bayes_adaptive`, `bayes_ev` | Additional equity and opponent-model variants | Comparison candidates |

Historical `m5_challenger` results before the adaptive turn-pressure upgrade describe the strategy now preserved as `m5_classic`. The existing M6, M8–M11, and Cherki policies retain that classic dependency so their behavior is not silently changed.

Historical results called `m6_counter` refer to the policy now stored as `m5_counterplay` (Talon), as documented in `league/results_notes.md`. Historical rows using the same ID can also represent different code versions: check their notes and commit before comparing them.

## Adding a bot with teammates

Choose a unique descriptive runnable ID, search the existing `bots/` directory and this catalog first, and add a catalog row in the same change. Avoid reusing an ID or changing its implementation to represent a different experiment; copy it to a new ID instead. Record the commit, training data or table, seed ranges, opponents, and settings with benchmark results. Fetch before pushing and integrate teammate changes without rewriting their results. Existing IDs stay valid so old commands and CSVs remain interpretable.

The teammate branch `codex/method1` at `ada47a27d4ee06a93e75af2f4a7c3a9fc4d01f24` is preserved; Hawk is its tuned policy imported under a separate ID with its optimized equity sampler, so the shared `m1_equity` policy and dependent bots retain their existing behavior. The branch’s historical CSV is saved separately at `league/benchmarks/method1_branch_ada47a2.csv`; branch rows use their original names and must be interpreted with that branch’s notes.

Cherki was merged from `main` in commit `4036849`; historical results called `m11_combined` refer to Cherki versions, as detailed in `league/results_notes.md`. Rangefinder was imported unchanged from branch `codex/rangefinder` at `b8337b1`; its branch remains intact.
