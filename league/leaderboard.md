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
