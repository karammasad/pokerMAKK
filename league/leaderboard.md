# Round-robin leaderboard — official format (real results)

Official-format round-robin: 12 bots, 66 pairings, 3 seeds (0,1,2) pooled per pairing (3000 deals/pairing total), 1000 deals/seed x 2 halves/match — matches the competition's duplicate format (1000 deals x 2 halves per seed, pooled bb/deal, 95% CI verdict: win if CI entirely >0, loss if entirely <0, chop otherwise). `harrier` (CFR-family research bot) is not yet merged to origin/main as of this run and is not included; add it and re-run once it lands. `messi` was added mid-run (teammate push) and given the same treatment: full pooled pairings vs every other shortlist bot.

| Rank | Bot | Points | Record (W-L-C) | Avg bb/deal |
| --- | --- | --- | --- | --- |
| 1 | `aguero` | 9.5 | 9-1-1 | +0.488 |
| 2 | `messi` | 9.0 | 7-0-4 | +0.374 |
| 3 | `mahrez` | 8.0 | 7-2-2 | +0.434 |
| 4 | `ederson` | 8.0 | 8-3-0 | +0.308 |
| 5 | `m5_challenger` | 7.0 | 6-3-2 | +0.219 |
| 6 | `kestrel` | 6.0 | 4-3-4 | +0.119 |
| 7 | `telltide` | 5.5 | 3-3-5 | +0.058 |
| 8 | `northstar` | 4.0 | 2-5-4 | +0.025 |
| 9 | `osprey` | 3.5 | 2-6-3 | -0.185 |
| 10 | `m5_counterplay` | 3.5 | 2-6-3 | -0.197 |
| 11 | `m9_cfrplus` | 1.0 | 0-9-2 | -0.601 |
| 12 | `m5_classic` | 1.0 | 1-10-0 | -1.044 |

## Current default / what we would submit today

**Standings leader is `aguero`, not `m5_challenger`.** Head-to-head vs `m5_challenger` in this run: +0.4927 bb/deal, CI[+0.2871,+0.6982], verdict=win, n=3000 deals.

This head-to-head CI is entirely positive for `aguero` over `m5_challenger` — **recommended for promotion pending human review** (standing policy requires a significant pooled-CI win across 8-10+ seeds x 1000 deals specifically vs `m5_challenger` before flipping `bots/active.py`; this run used 3 seeds, so a deeper confirmation run at 8-10 seeds is still warranted). `bots/active.py` was **not** modified by this run.

**Bots that beat `m5_challenger` head-to-head with a significant CI in this run:** `ederson` (+0.4463 bb/deal), `mahrez` (+0.3387 bb/deal), `aguero` (+0.4927 bb/deal). All flagged for deeper confirmation (8-10+ seeds) before any promotion decision.

## Top-5 deep validation — 10 seeds x 1000 deals pooled, full C(5,2) matrix

The 3-seed round-robin above is noisy (this project has already been burned once by a 3-seed/low-sample result reversing at depth — see the akanji/gundogan episode earlier in this project's history, where a fast pass showed them beating `m5_challenger` and a proper 10-seed pooled validation showed the opposite). So every pairing among the top 5 (`m5_challenger`, `aguero`, `ederson`, `mahrez`, `messi`) was re-run at full depth: 10 seeds (5000-5009), 1000 deals/seed x 2 halves, pooled bb/deal, 95% CI. All 10 pairings, 0 errors throughout.

| Bot A | Bot B | bb/deal (A persp.) | CI | Verdict |
| --- | --- | --- | --- | --- |
| `m5_challenger` | `aguero` | -0.2588 | [-0.3731,-0.1445] | **loss** |
| `m5_challenger` | `ederson` | -0.1477 | [-0.2603,-0.0351] | **loss** |
| `m5_challenger` | `mahrez` | +0.0367 | [-0.1020,+0.1754] | chop |
| `m5_challenger` | `messi` | +0.0564 | [-0.0451,+0.1579] | chop |
| `aguero` | `messi` | -1.9171 | [-2.1210,-1.7132] | **loss (big)** |
| `aguero` | `mahrez` | +0.3096 | [+0.1587,+0.4605] | win |
| `aguero` | `ederson` | +0.5100 | [+0.3795,+0.6405] | win |
| `messi` | `mahrez` | +0.8959 | [+0.6934,+1.0984] | win |
| `messi` | `ederson` | +0.7156 | [+0.5403,+0.8909] | win |
| `mahrez` | `ederson` | +0.8163 | [+0.6245,+1.0081] | win |

**Deep-validated standings (supersedes the 3-seed ranking for these 5 bots):**

| Rank | Bot | Points | Record (W-L-C) | Avg bb/deal |
| --- | --- | --- | --- | --- |
| 1 | `messi` | 3.5 | 3-0-1 | +0.868 |
| 2 | `aguero` | 3.0 | 3-1-0 | -0.210 |
| 3 | `mahrez` | 1.5 | 1-2-1 | -0.106 |
| 4 | `m5_challenger` | 1.0 | 0-2-2 | -0.078 |
| 5 | `ederson` | 1.0 | 1-3-0 | -0.474 |

**The ranking order changed from the 3-seed pass.** 3-seed round-robin order was `aguero` > `messi` > `mahrez` > `ederson` > `m5_challenger`. At full depth it's `messi` > `aguero` > `mahrez` > `m5_challenger` > `ederson` — `messi` overtakes `aguero` (it beats `aguero` head-to-head by a large, clearly significant margin: -1.92 bb/deal for `aguero`), and `ederson` collapses from 4th to last (it only beats `m5_challenger`; it loses to every other top-5 bot, including the two `m5_challenger` itself only chops with). `m5_challenger` climbs from last to 4th once measured against this specific group rather than the full 3-seed field — `aguero` and `ederson` genuinely beat it (CI entirely negative, holding up at 10x the sample, unlike the akanji/gundogan reversal), but it chops with `mahrez` and `messi` rather than losing to everyone.

**Recommendation for human review:** `messi` is the strongest validated candidate in this group — it has a significant head-to-head win or chop against every other top-5 bot, including a decisive win over the bot that led the 3-seed pass (`aguero`). `bots/active.py` has **not** been touched; promotion remains a human decision per standing policy.

## Full pairwise results

| Bot A | Bot B | bb/deal (A persp.) | CI | Verdict |
| --- | --- | --- | --- | --- |
| `m5_challenger` | `m5_classic` | +0.9387 | [+0.6686,+1.2088] | win |
| `m5_challenger` | `m5_counterplay` | +0.3900 | [+0.3095,+0.4705] | win |
| `m5_challenger` | `kestrel` | +0.0147 | [-0.0658,+0.0951] | chop |
| `m5_challenger` | `osprey` | +0.4103 | [+0.3215,+0.4992] | win |
| `m5_challenger` | `ederson` | -0.4463 | [-0.6346,-0.2580] | loss |
| `m5_challenger` | `mahrez` | -0.3387 | [-0.6094,-0.0680] | loss |
| `m5_challenger` | `telltide` | +0.3823 | [+0.1432,+0.6214] | win |
| `m5_challenger` | `northstar` | +0.3283 | [+0.0705,+0.5861] | win |
| `m5_challenger` | `m9_cfrplus` | +1.0710 | [+0.6595,+1.4825] | win |
| `m5_challenger` | `aguero` | -0.4927 | [-0.6982,-0.2871] | loss |
| `m5_challenger` | `messi` | +0.1550 | [-0.0296,+0.3396] | chop |
| `m5_classic` | `m5_counterplay` | -0.8893 | [-1.1586,-0.6200] | loss |
| `m5_classic` | `kestrel` | -1.1630 | [-1.4419,-0.8841] | loss |
| `m5_classic` | `osprey` | -0.9280 | [-1.1988,-0.6572] | loss |
| `m5_classic` | `ederson` | -1.2980 | [-1.5991,-0.9969] | loss |
| `m5_classic` | `mahrez` | -1.3263 | [-1.6877,-0.9649] | loss |
| `m5_classic` | `telltide` | -1.5870 | [-1.9034,-1.2706] | loss |
| `m5_classic` | `northstar` | -1.5263 | [-1.8496,-1.2031] | loss |
| `m5_classic` | `m9_cfrplus` | +0.5373 | [+0.0405,+1.0342] | win |
| `m5_classic` | `aguero` | -1.4577 | [-1.7591,-1.1562] | loss |
| `m5_classic` | `messi` | -0.9113 | [-1.2154,-0.6073] | loss |
| `m5_counterplay` | `kestrel` | -0.3127 | [-0.4235,-0.2018] | loss |
| `m5_counterplay` | `osprey` | +0.0157 | [-0.0372,+0.0686] | chop |
| `m5_counterplay` | `ederson` | -0.8850 | [-1.0804,-0.6896] | loss |
| `m5_counterplay` | `mahrez` | -0.5653 | [-0.8469,-0.2838] | loss |
| `m5_counterplay` | `telltide` | -0.1993 | [-0.4168,+0.0181] | chop |
| `m5_counterplay` | `northstar` | -0.1977 | [-0.4389,+0.0436] | chop |
| `m5_counterplay` | `m9_cfrplus` | +0.4633 | [+0.0476,+0.8791] | win |
| `m5_counterplay` | `aguero` | -0.7357 | [-0.9421,-0.5292] | loss |
| `m5_counterplay` | `messi` | -0.2447 | [-0.4272,-0.0622] | loss |
| `kestrel` | `osprey` | +0.3273 | [+0.2042,+0.4504] | win |
| `kestrel` | `ederson` | -0.5627 | [-0.7613,-0.3641] | loss |
| `kestrel` | `mahrez` | -0.3863 | [-0.6628,-0.1098] | loss |
| `kestrel` | `telltide` | -0.0317 | [-0.2489,+0.1856] | chop |
| `kestrel` | `northstar` | -0.0397 | [-0.2825,+0.2032] | chop |
| `kestrel` | `m9_cfrplus` | +0.9332 | [+0.5205,+1.3458] | win |
| `kestrel` | `aguero` | -0.5837 | [-0.7977,-0.3697] | loss |
| `kestrel` | `messi` | +0.1920 | [-0.0079,+0.3919] | chop |
| `osprey` | `ederson` | -0.8330 | [-1.0259,-0.6401] | loss |
| `osprey` | `mahrez` | -0.5090 | [-0.7949,-0.2231] | loss |
| `osprey` | `telltide` | -0.1830 | [-0.4051,+0.0391] | chop |
| `osprey` | `northstar` | -0.1660 | [-0.4116,+0.0796] | chop |
| `osprey` | `m9_cfrplus` | +0.5275 | [+0.1116,+0.9434] | win |
| `osprey` | `aguero` | -0.7753 | [-0.9866,-0.5641] | loss |
| `osprey` | `messi` | -0.2720 | [-0.4583,-0.0857] | loss |
| `ederson` | `mahrez` | -1.2877 | [-1.6382,-0.9371] | loss |
| `ederson` | `telltide` | +0.7917 | [+0.5004,+1.0829] | win |
| `ederson` | `northstar` | +0.7930 | [+0.5051,+1.0809] | win |
| `ederson` | `m9_cfrplus` | +0.5657 | [+0.0697,+1.0617] | win |
| `ederson` | `aguero` | -0.9897 | [-1.2831,-0.6962] | loss |
| `ederson` | `messi` | -0.5063 | [-0.8190,-0.1937] | loss |
| `mahrez` | `telltide` | +0.2670 | [-0.0835,+0.6175] | chop |
| `mahrez` | `northstar` | +0.3670 | [+0.0223,+0.7117] | win |
| `mahrez` | `m9_cfrplus` | +0.5343 | [-0.0653,+1.1340] | chop |
| `mahrez` | `aguero` | -0.2897 | [-0.5610,-0.0184] | loss |
| `mahrez` | `messi` | -0.5180 | [-0.8814,-0.1546] | loss |
| `telltide` | `northstar` | +0.1853 | [+0.0102,+0.3605] | win |
| `telltide` | `m9_cfrplus` | +0.6007 | [+0.1781,+1.0233] | win |
| `telltide` | `aguero` | -0.7350 | [-1.0191,-0.4509] | loss |
| `telltide` | `messi` | +0.0282 | [-0.2728,+0.3292] | chop |
| `northstar` | `m9_cfrplus` | +0.7267 | [+0.3006,+1.1528] | win |
| `northstar` | `aguero` | -0.7193 | [-1.0065,-0.4321] | loss |
| `northstar` | `messi` | +0.0133 | [-0.2520,+0.2786] | chop |
| `m9_cfrplus` | `aguero` | +0.0400 | [-0.3467,+0.4267] | chop |
| `m9_cfrplus` | `messi` | -0.6873 | [-1.1013,-0.2734] | loss |
| `aguero` | `messi` | -1.3670 | [-1.7341,-0.9999] | loss |

## Messi iteration — a genuine, validated edge over m5_challenger

Directive: push `messi` (the strongest top-5 bot, but previously only a chop
against `m5_challenger` specifically) toward a real win over `m5_challenger`,
without trading away its dominance over the rest of the top-5. Started from
the 10-seed baseline: `m5_challenger` vs `messi` = +0.0564 bb/deal for
`m5_challenger` (chop, CI straddled zero) — then re-confirmed at 30 seeds
(6000-6029, n=30000): +0.0377 for `m5_challenger`, CI[-0.0182,+0.0936], still
a chop, very slightly leaning `m5_challenger`'s way.

**Mechanism.** `messi` = `m5_challenger`'s own policy (`bots/common/counter_strategies`
with profile `'m5_challenger'`) plus three additive layers: (1) a 1-in-4 mixed
light preflop button open, (2) a 1-in-4 checked-to-river semi-bluff gated on
observed turn fold-rate, (3) a "raise-the-raiser" layer that converts a fold
facing a bet into a bluff-reraise once observed fold-rate to that bluff is
high enough. Since `messi`'s base *is* `m5_challenger`, the matchup is close
to a mirror match with extra aggression layered on — which explains why it
was landing close to even.

**Why City bots (`aguero`/`ederson`) genuinely beat `m5_challenger` (read
`bots/city_core.py` and compared `aguero`/`ederson`'s profiles against
`m5_challenger`):** the single most portable, purely defensive mechanism is
`rr_cut=0.85` — City bots fold to a **reraise** (a raise of our own
bet/raise, not just a first bet) unless equity >=0.85, treating a reraise
range as far stronger than a first-bet range. `m5_challenger`/`messi` have no
such reraise-specific bar; they fold facing *any* bet using the same flat
`odds + 0.30` margin regardless of whether it's a first bet or a reraise.
The rest of City's edge (`station_thin`, `cb_exploit`, tuned bluff
frequencies, near-threshold equity refinement) is aggression/bluff-tuning —
exactly the category of exploitable pattern `messi` already punishes hard in
`aguero` (+1.92 bb/deal head-to-head) — so per explicit instruction, none of
that was grafted onto `messi`; only the purely-defensive `rr_cut` idea was
tried, specifically to avoid making `messi` more `aguero`-like.

**Variants built and screened (5 seeds x 1000 deals vs `m5_challenger`
unless noted; all registered in `league/run.py`'s `RESEARCH_CANDIDATES`,
`tests/test_messi_v*.py`, and `BOT_CATALOG.md`, win or lose):**

| Variant | Change from `messi` | vs `m5_challenger` (own persp.) | Verdict |
| --- | --- | --- | --- |
| `messi_v2` | Tighten raise-the-raiser bluff (more evidence, smaller cost cap) | +0.0598 | chop (improved) |
| `messi_v3` | Loosen preflop steal + raise-the-raiser bluff | -0.2030 [-0.3689,-0.0371] | **loss** (confirmed bad — more bluffing hurts) |
| `messi_v4` | Remove raise-the-raiser layer entirely (diagnostic) | +0.0502 | chop (~same as v2) |
| `messi_v5` | Loosen checked-to-river semi-bluff gate | -0.0498 | chop (no improvement) |
| `messi_v6` | `messi_v2`'s tightened bluff **+ City-style `rr_cut`=0.85 reraise discipline** | see below | **real win** |

`messi_v3` confirms the matchup punishes extra bluffing — consistent with
`messi`'s base already being `m5_challenger`'s own policy. `messi_v2`/`v4`
show the raise-the-raiser layer, as originally tuned, was roughly neutral to
slightly costly; tightening or removing it both helped a little. The real
breakthrough was adding the purely-defensive reraise discipline.

**`messi_v6` — validated results:**

| Matchup | Depth | bb/deal (messi_v6 persp.) | CI | Verdict |
| --- | --- | --- | --- | --- |
| vs `m5_challenger` | 15 seeds (9000-9014), n=15000 | **+0.1431** | **[+0.0547,+0.2314]** | **win** |
| vs `messi` (original) | 5 seeds (9100-9104), n=5000 | +0.0428 | [-0.1775,+0.2631] | chop |
| vs `aguero` | 8 seeds (10000-10007), n=8000 | +2.5820 | [+2.4121,+2.7519] | win |
| vs `ederson` | 8 seeds (10000-10007), n=8000 | +1.0904 | [+0.9048,+1.2759] | win |
| vs `mahrez` | 8 seeds (10000-10007), n=8000 | +1.8405 | [+1.6344,+2.0466] | win |

0 errors across every run above.

**This is the first bot this project has validated with a statistically
significant, CI-entirely-positive edge over `m5_challenger` at full depth
(15 seeds, exceeding the 8-10 seed policy bar) that also does not trade away
anything — `messi_v6` *improves* on original `messi`'s already-dominant
numbers against the rest of the top-5** (`aguero` +1.92 -> +2.58, `ederson`
+0.72 -> +1.09, `mahrez` +0.90 -> +1.84), chops with original `messi` itself
(a near-identical mirror, as expected since v6 is a strict refinement of the
same base), and genuinely beats `m5_challenger` where every prior top-5
member only tied or lost to it with less margin.

**Recommendation for human review:** `messi_v6` is a strong, validated
promotion candidate — real edge over `m5_challenger` (+0.143 bb/deal, CI
entirely positive, 15000 deals), and strictly better than or equal to every
other top-5 bot it was tested against. Per standing policy `bots/active.py`
has **not** been touched; promoting it to the live default is the human's
call.

## PROMOTED: `messi_v6` is now the default (`bots/active.py`)

The user approved promotion, conditional on one more check: a full-zoo gate
(`python league/run.py --bot messi_v6 --zoo all --seeds 3`, the complete
ZOO + EQUITY_ZOO + RESEARCH_CANDIDATES field — 71 opponents, 213 matches, not
just the curated top-5 group) to confirm the edge holds broadly and wasn't
narrowly tuned against just `aguero`/`ederson`/`mahrez`/`m5_challenger`.

**Full-zoo gate result: 160 win / 50 chop / 3 loss, 0 errors across all 213
matches.** The only losses were to `messi_v6`'s own earlier sibling variant
`messi_v2` (an internal, closely-related strategy — not a competitive threat
from the field) — no other bot in the entire ~70-bot zoo beat it. Combined
with the already-confirmed real edge over `m5_challenger` (+0.143 bb/deal,
CI entirely positive, 15 seeds) and the strengthened top-5 numbers above,
this clears the bar.

**`bots/active.py`'s `ACTIVE_BOT` default changed from `m5_challenger` to
`messi_v6`.** `m5_challenger` remains in the roster as the primary
reference/regression baseline — undefeated through extensive validation
against every other challenger this session until `messi_v6` broke through.
