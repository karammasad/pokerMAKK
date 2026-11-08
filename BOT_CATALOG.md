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
| Rangeglass | `rangeglass` | Corrected single-shrink showdown range model | Research challenger |
| Telltide | `telltide` | Bayesian bet-response expected-value policy | Research challenger |
| Riverloom | `riverloom` | Sequential equity sampling near action thresholds | Research challenger |
| Suitspark | `suitspark` | Preflop-action-conditioned Short Deck PLO5 range equity | Research challenger |
| PebbleCFR | `pebble_cfr` | Sequence-aware MCCFR+ prototype with M5 fallback | Research prototype |
| Lens | `m7_precision` | Anchor with selective extra equity sampling | Comparison candidate |
| Guard | `equity_guarded` | Guarded equity portfolio policy | Comparison candidate |
| Scout | `m1_equity` | Original equity policy | Baseline |
| Shield | `m6_safeadapt` | Anchor with bounded response-based adjustments | Research comparator |
| Profiles | `m8_bayes_types` | Public-action type posterior | Research comparator |
| Regret | `m9_cfrplus` | Compact MCCFR+ table with fallback | Research comparator |
| Sequence | `m10_seq_cfr` | Sequence-aware MCCFR+ table with fallback | Research comparator |
| Methods 2–4 | `m2_cfr`, `m3_exploit`, `m4_learned` | Earlier experimental policies | Research comparators |
| MCCFR | `mccfr` | Earlier sequential MCCFR prototype | Research comparator |
| Portfolio | `equity_core`, `equity_pressure`, `equity_precise`, `bayes_adaptive`, `bayes_ev` | Additional equity and opponent-model variants | Comparison candidates |

Historical `m5_challenger` results before the adaptive turn-pressure upgrade describe the strategy now preserved as `m5_classic`. The existing M6, M8–M11, and Cherki policies retain that classic dependency so their behavior is not silently changed.

Historical results called `m6_counter` refer to the policy now stored as `m5_counterplay` (Talon), as documented in `league/results_notes.md`. Historical rows using the same ID can also represent different code versions: check their notes and commit before comparing them.

## Adding a bot with teammates

Choose a unique descriptive runnable ID, search the existing `bots/` directory and this catalog first, and add a catalog row in the same change. Avoid reusing an ID or changing its implementation to represent a different experiment; copy it to a new ID instead. Record the commit, training data or table, seed ranges, opponents, and settings with benchmark results. Fetch before pushing and integrate teammate changes without rewriting their results. Existing IDs stay valid so old commands and CSVs remain interpretable.
