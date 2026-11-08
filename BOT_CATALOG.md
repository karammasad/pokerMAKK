# Poker bot catalog

These are human-readable labels for discussion. The **runnable ID** remains the exact module or portfolio name used by `POKER_BOT`, the league runner, and historical CSV rows. A label does not imply that a bot is the strongest. Select an entry with `POKER_BOT=<runnable ID>` or `league/run.py --bot <runnable ID>`.

| Label | Runnable ID | Description | Status |
| --- | --- | --- | --- |
| Atlas | `atlas` | Aguero-derived complete response accounting, confidence-gated counterplay and prefix-reusable Monte Carlo | Frozen validated baseline; paired leader-pool gain over Aguero |
| Atlas Learning | `atlas_learning` | Atlas plus bounded outcome feedback for marginal river calls | Challenger; fresh confirmation positive, final full-zoo verification in progress; selectable with POKER_BOT |
| Messi | `messi` | Adaptive pressure with response-gated reraises and a late-half timing guard | Research challenger; chops m5_challenger at 30-seed pooled depth |
| Messi v2 | `messi_v2` | Messi with a tightened raise-the-raiser bluff (more evidence, smaller cost cap) | Research challenger; screened only (5 seeds) |
| Messi v3 | `messi_v3` | Messi with a looser preflop steal and looser raise-the-raiser bluff | Research challenger; confirmed loser vs m5_challenger (5-seed screen, CI entirely negative) |
| Messi v4 | `messi_v4` | Messi with the raise-the-raiser bluff removed entirely (diagnostic variant) | Research challenger; screened only (5 seeds) |
| Messi v5 | `messi_v5` | Messi with a looser checked-to-river semi-bluff gate | Research challenger; screened only (5 seeds), no improvement |
| Messi v6 | `messi_v6` | Messi v2's tightened bluff plus a City-engine-style reraise-discipline fold (fold to a reraise unless equity >=0.85) | Prior validated champion, superseded by messi_v10. Validated beating m5_challenger head-to-head (+0.143 bb/deal, CI[+0.055,+0.231], 15 seeds x 1000 deals pooled) and strengthened wins over aguero/ederson/mahrez vs plain messi. Full `--zoo all --seeds 3` gate: 160 win / 50 chop / 3 loss (losses only to sibling variant messi_v2), 0 errors. Kept as a reference/regression baseline; not deleted. |
| Messi v7 | `messi_v7` | Frequency-adaptive reraise threshold, recovered unchanged from existing worktree | Research comparator; response observations are censored when hands end or streets complete. Independent 10 seeds (29000–29009) × 1000 deals vs v6: +0.1763 bb/deal, 95% CI [+0.0775, +0.2751]. Three-seed full zoo: 153 wins / 75 chops / 0 losses, 0 errors and fallbacks; max 2.505 s per half. Beats v6 but only chops m5_challenger directly (not a validated win vs the actual target) — a separate concurrent session promoted this to entry default locally, but that was never pushed and `messi_v10` (validated beating m5_challenger, not just v6) is the correct live default. Kept as a research comparator, not promoted. |
| Messi showdown range | `messi_showdownrange` | V7 with prior-shrunk showdown range evidence for marginal postflop calls | Research candidate; 5-seed screen vs v7: -0.0276 bb/deal, 95% CI [-0.0891, +0.0339]; vs v2: -0.0190 ([-0.0936, +0.0556]); both chops. Zero errors/fallbacks; not advanced to zoo. |
| Messi Bayes | `messi_bayes` | V7 with Bayesian-shrunk reraise-frequency threshold | Research candidate; 3-seed screen: +0.0313 bb/deal vs v7 (95% CI [-0.0486, +0.1113]) and -0.0050 vs v2 ([-0.0947, +0.0847]); both chops. Not advanced to full zoo. |
| Messi response | `messi_response` | V7-style adaptive threshold with first postflop raise responses tracked across streets and terminal folds/calls | Research candidate; 10 seeds (28000–28009) × 1000 deals vs v6: +0.0108 bb/deal, 95% CI [-0.0349, +0.0565], chop; not promoted. Three-seed full zoo: 172 wins / 51 chops / 5 losses, 0 errors and fallbacks; max 2.696 s per half. |
| Messi river probe | `messi_riverprobe` | V7 plus cost-limited river bluffs gated by observed river-bet fold rate | Research candidate; 3-seed screen vs v7 +0.0083 bb/deal, 95% CI [-0.0137, +0.0303], chop; not promoted. Three-seed full zoo: 163 wins / 67 chops / 1 loss, 0 errors and fallbacks; maximum 2.403 s per half. |
| Anchor | `m5_challenger` | Adaptive turn pressure over the counterplay equity policy | Prior champion; undefeated through extensive validation against every other challenger this session until messi_v6. Kept as the primary reference/regression baseline. |
| Messi v9 | `messi_v9` | messi_v6 plus a City-engine-style thin-value-vs-stations rule (bet weaker hands for value when a generic make/fold counter shows the opponent rarely folds to our aggression; half_cut 0.375->0.335, pot_cut 0.76->0.73, mirroring `ederson`'s `station_thin`) | Research candidate, NOT promoted. Beats m5_challenger even better than v6 (+0.284 bb/deal at 4 seeds, +0.175 at 12 seeds, CI[+0.083,+0.266]) and crushes aguero (+2.78)/ederson (+0.75), but opens a new, real loss against the base messi lineage itself: loses to plain `messi` (-0.361, CI entirely negative) and badly to `messi_v2` (-1.156, CI entirely negative), and loses to `messi_v6` (-0.158). The thin value bets appear to telegraph medium-strength hands that messi's own evidence-gated reads exploit. Kept as a documented cautionary data point for the next iteration. |
| Messi v10 | `messi_v10` | messi_v9's station-thin mechanism with a much higher evidence bar (made>=70 vs 40, fold-rate<0.12 vs 0.20) and a smaller threshold shift (half_cut 0.375->0.355, pot_cut 0.76->0.745) | **Current entry default.** Promoted over messi_v6 after human review: beats m5_challenger by MORE than messi_v6 does (+0.210 bb/deal, CI[+0.121,+0.299], 12 seeds x 1000 deals pooled, vs v6's +0.143). Fixes v9's sibling regressions: chops (does not lose to) plain `messi` and `messi_v6`. Still beats aguero (+2.49) and ederson (+1.17) decisively. Full `--zoo all --seeds 3` gate: 176 win / 49 chop / 3 loss, 0 errors -- a strictly better zoo record than v6's 160/50/3 with the same loss pattern (all 3 to messi_v2, a persistent structural counter to this whole rr_cut/station family that no variant in this lineage has fixed yet). A separate, unvalidated promotion of `messi_v7` (which only ties m5_challenger, not a real win) was superseded by this one. |
| Harrier | `harrier` | Extends Talon (`m5_counterplay`) with SPR-shifted call-defense thresholds and a blocker-gated semi-bluff on top of Kestrel's fold-rate evidence gate | Research candidate, not promoted. Pooled over 10 seeds x 1000 deals vs m5_challenger: -0.295 bb/deal, 95% CI [-0.351,-0.239] — a clean, statistically significant loss. |
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
| Northstar | `northstar` | Telltide with evidence-gated large river-call adaptation | Experimental challenger |
| River Ruse | `river_ruse` | River pot-bet pressure sparring policy | Sparring opponent |
| Undertow | `undertow` | Telltide with threshold-based extra equity samples | Experimental challenger |
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
| Aguero | `aguero` | City engine plus a cross-hand opponent model: per-street fold response gates bluffs, preflop fold rate widens opens, showdown reads of bet/call strength adjust call margins and re-raise folds | City family candidate (in evaluation) |
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
| Osprey | `osprey` | Talon with postflop equity estimated against a reweighted opponent-hand particle filter instead of a uniform random hand | Research candidate, not promoted (pooled -0.41 bb/deal vs m5_challenger over 10k deals, essentially Talon's own baseline deficit; beats the rest of the zoo: 85 win / 48 chop / 17 loss over the single-seed `--zoo all` gate) |
| Equity sparring | `equity_balanced`, `equity_tight`, `equity_loose` | Teammate's frozen-equity threshold variants | In-process sparring opponents |
| Portfolio | `equity_core`, `equity_pressure`, `equity_precise`, `bayes_adaptive`, `bayes_ev` | Additional equity and opponent-model variants | Comparison candidates |

Historical `m5_challenger` results before the adaptive turn-pressure upgrade describe the strategy now preserved as `m5_classic`. The existing M6, M8–M11, and Cherki policies retain that classic dependency so their behavior is not silently changed.

Historical results called `m6_counter` refer to the policy now stored as `m5_counterplay` (Talon), as documented in `league/results_notes.md`. Historical rows using the same ID can also represent different code versions: check their notes and commit before comparing them.

## Adding a bot with teammates

Choose a unique descriptive runnable ID, search the existing `bots/` directory and this catalog first, and add a catalog row in the same change. Avoid reusing an ID or changing its implementation to represent a different experiment; copy it to a new ID instead. Record the commit, training data or table, seed ranges, opponents, and settings with benchmark results. Fetch before pushing and integrate teammate changes without rewriting their results. Existing IDs stay valid so old commands and CSVs remain interpretable.

The teammate branch `codex/method1` at `ada47a27d4ee06a93e75af2f4a7c3a9fc4d01f24` is preserved; Hawk is its tuned policy imported under a separate ID with its optimized equity sampler, so the shared `m1_equity` policy and dependent bots retain their existing behavior. The branch’s historical CSV is saved separately at `league/benchmarks/method1_branch_ada47a2.csv`; branch rows use their original names and must be interpreted with that branch’s notes.

Cherki was merged from `main` in commit `4036849`; historical results called `m11_combined` refer to Cherki versions, as detailed in `league/results_notes.md`. Rangefinder was imported unchanged from branch `codex/rangefinder` at `b8337b1`; its branch remains intact.
