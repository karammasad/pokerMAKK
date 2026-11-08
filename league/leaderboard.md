# Round-robin roster shortlist

Scope note: this file currently holds a **roster recommendation only** — which
bots to include in a round-robin, not round-robin results. The actual
official-format round-robin (1000 deals x 2 halves per pairing, pooled bb/deal,
95% CI verdict, matching the competition's duplicate format) is deferred: the
user wants to design a prompt for teammates to run that tournament themselves,
as a separate follow-up. This file exists so that prompt can start from an
already-curated field instead of all ~46 `bots/` directories.

Methodology for the cut: read `BOT_CATALOG.md` and the full `league/results.csv`
history, aggregated by opponent name (pooling every match ever recorded against
`m5_challenger`, sign-corrected to `m5_challenger`'s perspective). Historical
rows are **not fully trustworthy on their own** — `m5_challenger`'s own code
changed mid-project (that's why `m5_classic` exists, as the frozen pre-refactor
snapshot), so old rows can reflect a weaker version of `m5_challenger` than the
one in the repo today. Every bot with no fresh data, or with a historical
signal that looked surprising (e.g. the full "first City family" — foden,
bernardo, rodri, haaland, de_bruyne, grealish — showed `m5_challenger` *losing*
by -0.5 to -1.0 bb/deal in old rows), got a fresh cheap sanity check this pass
(single seed, 150 deals, current code) before being cut or kept. 150-deal
single-seed results are directional only — notably, `akanji` showed a *loss*
for `m5_challenger` at this cheap setting, which is the same low-sample noise
that misled an earlier pass in this project; the properly validated number
(10 seeds x 1000 deals pooled, from earlier this session) is `m5_challenger`
**beating** `akanji` and `gundogan` by +0.27-0.28 bb/deal with the CI entirely
positive. Don't re-litigate that; it's settled.

## Keep (shortlist for the round-robin) — 11 bots

| Bot | Why kept |
| --- | --- |
| `m5_challenger` | Current anchor/default (`bots/active.py`). Repeatedly validated champion this session against every challenger tried (Kestrel, Osprey, Harrier, both City families). The bar everything else is measured against. |
| `m5_classic` | Frozen pre-refactor M5. Useful fixed reference point to see how far the field (including `m5_challenger` itself) has moved; several other bots (`m11_chosen`, `m7_cherki`) intentionally depend on this frozen version rather than current `m5_challenger`. |
| `m5_counterplay` (Talon) | Distinct postflop-pressure lineage; feeds Kestrel and others. Historically the closest sustained rival to `m5_challenger` (9W-6L vs m5, no chops — genuinely contested, not just noise). |
| `kestrel` | Talon + evidence-gated semi-bluff (turn+river). Most competitive challenger on record: 4W-4L-38C vs `m5_challenger`, net avg ~0 bb/deal across 46 historical matches — essentially a coin flip. Worth a real multi-seed look. |
| `osprey` | Range-aware particle-filter equity (opponent-hand reweighting) instead of equity-vs-random. Already validated this session: loses to `m5_challenger` (-0.41 bb/deal, CI negative) but beats the rest of the zoo soundly (85W/48C/17L). Structurally the most distinct opponent-modeling approach in the roster. |
| `ederson` | City-engine "adaptive exploiter" (bluffs folders, thins value vs stations). Most competitive City-family variant on record (near-even, -0.1 avg) and a fresh check this pass confirmed it's still close (chop at seed 55000). Kept as the family's single representative. |
| `mahrez` | City-engine "ballsy" aggressive outlier (overbluffs, floats, bluff-raises, stop-loss). Deliberately different risk profile from every other bot in the roster — good stress-test/diversity pick even though BOT_CATALOG flags it as exploitable by turn-pressure bots. |
| `telltide` | Bayesian bet-response expected-value policy — distinct mechanism (posterior over bet-response types) from every equity-based bot above. Large historical sample (35 matches), fairly close to `m5_challenger` (+0.13 avg, mostly chops). |
| `northstar` | Telltide + evidence-gated large river-call adaptation. Actually beat `m5_challenger` in 3 of its historical current-code matches (3W-2L-13chop net +0.12) — one of only two bots in the whole catalog with any recorded current-code wins against the anchor. Worth a real multi-seed look. |
| `m9_cfrplus` | Compact MCCFR+ table with fallback — the clearest surviving CFR-family / academic-technique representative (per the user's standing "frontier technology" directive) with no disqualifying data against it yet. Paired with `m5_counterplay`/Talon and `osprey`, keeps the roster's mechanisms genuinely diverse rather than N variations on equity estimation. |
| `aguero` | Newest bot (just landed from a teammate, City engine + cross-hand opponent model that rewrites its profile every decision within a half). No real validation yet — a single quick check even showed a loss for `m5_challenger` — but it's too new and structurally distinct (learns across hands, not just within one) to cut sight-unseen. Flagged as "needs the real round-robin before anyone trusts this result." |

`harrier` (CFR-family academic-research bot, built independently this session)
is not yet merged to `origin/main` as of this cut — it's still being finished
by a concurrent effort. **Add it to the shortlist once it lands**; it's the
other dedicated academic/frontier-technique effort from this session and
belongs alongside `m9_cfrplus`.

## Cut — with rationale

| Bot(s) | Rationale |
| --- | --- |
| `m1_equity`, `m1_reference`, `m1_team_tuned` | Foundational baseline equity bots; already clearly dominated by `m5_challenger` (e.g. `m1_equity`: 11W-0L-3chop against it). Useful as regression baselines, not round-robin contenders. |
| `m2_cfr`, `m3_exploit`, `m4_learned`, `m10_seq_cfr`, `pebble_cfr`, `mccfr` | Early experimental prototypes. Every recorded match has `m5_challenger` winning by +1.6 to +7 bb/deal. Clearly uncompetitive legacy methods. |
| `m6_safeadapt` | Fresh check this pass: loses to `m5_challenger` by +3.3 bb/deal (single seed, 150 deals). Not close. |
| `m8_bayes_types`, `rangefinder`, `rangeglass`, `riverloom`, `suitspark` | No standout signal in either direction, and mechanically redundant with `telltide`/`osprey` (already-kept Bayesian/opponent-modeling approaches). Cut for redundancy, not weakness. |
| `m7_precision`, `m7_cherki`, `m11_chosen`, `rook_fast` | Hybrid/precision variants built on the frozen `m5_classic` or `m5_counterplay`. All confirmed current-code losers to `m5_challenger` (0 wins across ~29 combined historical matches). `kestrel` and `m5_counterplay` already represent this lineage, and more competitively. |
| `river_ruse` | BOT_CATALOG explicitly labels this a "sparring opponent" (practice/test bot), not a real contender. |
| `mirrorfin`, `nightjar`, `tidehunter`, `turnblade`, `duskfox` | A cluster of minor turn/river-pressure tweaks on the Talon lineage. Fresh checks this pass: all land within a hair of 0 bb/deal (near-identical chops, no distinct signal from each other or from `kestrel`). Redundant as a group; cut entirely. |
| `akanji`, `gundogan`, `doku`, `stones`, `haaland`, `de_bruyne`, `rodri`, `foden`, `bernardo`, `grealish` | The rest of both City families (10 bots total). `akanji`/`gundogan` already properly validated (10-seed pooled) to lose to `m5_challenger` by +0.27-0.28 bb/deal, CI entirely positive. The rest got a fresh single-seed sanity check this pass: `foden`, `bernardo`, `rodri`, `haaland`, `de_bruyne`, `grealish` all won or chopped for `m5_challenger`, zero losses. All 10 share `bots/city_core.py` with just different `PROFILE` dicts — `ederson` and `mahrez` already cover this design family's most-competitive and most-distinct members; the rest are redundant near-duplicates. |
| `xavi` | Does not exist as a bot directory (checked: `bots/xavi/` is not present). Stale reference from an earlier directory listing; not a real bot. |

## Net result

46 bot directories -> **11 kept** (12 once `harrier` lands), covering every
genuinely distinct mechanism present in the codebase (anchor/equity lineage,
Talon pressure lineage + its semi-bluff extension, particle-filter opponent
modeling, Bayesian bet-response modeling, City-engine aggression variants,
CFR-family). This is the field recommended for the next, properly-run
official-format round-robin.
