# Rook and Talon evaluation

Rook is `m11_chosen`; Talon is `m5_counterplay`; Anchor is `m5_challenger`. Results below were produced locally on the source at `c5b6309` with the existing league engine and the added seed-range argument. Scores are big blinds per duplicate deal. League rows are appended to `league/results.csv`.

## Full pool screen

Rook played all 28 listed pool entries (including itself), seeds 0–2, 1,000 deals per match and both seats: 84 matches, 77 wins and 7 chops, zero losses, zero reported errors and zero Rook fallbacks. Three chops were self-play, three were versus Talon, and one was versus `m9_cfrplus`. The nine practice styles all lost in all three matches. Against Anchor, Rook scored +0.755, +0.785 and +0.842; against Lens (`m7_precision`), +0.564, +0.705 and +0.690. This screen includes historical development seeds and similar or duplicate styles; its match count is not an independent estimate of tournament win probability.

The worst recorded Rook thinking time was 4.670 seconds in a half, and three halves exceeded the repository's four-second target. All remained below the wrapper's six-second fallback threshold in this run. In-process wall-clock timing depends on machine load; verify under official container limits before selecting an entry.

## Separate same-seed comparison

Rook and Talon each played the same five opponents on seeds 900–902, 1,000 deals per seed and both seats. These seeds were not used in the full-pool screen. Entries show the average bb/deal across the three seeds; the difference is descriptive and is not a confidence interval for the paired comparison.

| Opponent | Rook | Talon | Rook minus Talon |
| --- | ---: | ---: | ---: |
| `shover` | +7.701 | +6.490 | +1.211 |
| `calling_station` | +7.700 | +8.041 | −0.341 |
| `always_pot` | +2.579 | +2.495 | +0.084 |
| `equity_guarded` | +1.463 | +1.561 | −0.099 |
| `m7_precision` | +0.417 | +0.504 | −0.087 |

All 30 matches had zero reported errors and zero candidate fallbacks. Six Rook halves exceeded four seconds, with a maximum 4.697 seconds. No conclusions about the tournament field can be drawn from this small, local opponent set.

## Prior official judge comparisons

In independent fresh-server duplicate matches, Rook beat Anchor on all ten 1,000-deal seeds 820–829, averaging +0.872 bb/deal (pooled 95% CI +0.721 to +1.023). Against Talon on five 1,000-deal seeds 840–844, Rook averaged +0.013 bb/deal (pooled 95% CI −0.044 to +0.071), with all five matches chopped. No errors were reported. These comparisons do not include actual entrant bots.

## Improvement priorities

1. Investigate preflop decisions against shoves and passive calling strategies. Rook and Talon share the same postflop implementation but use different preflop policies, making that the natural first place to inspect; the results do not establish which specific decisions cause the difference.
2. Reduce or budget postflop equity sampling and retest strength and time banks on fresh seeds. Preserve the existing snapshots as controls; changing sample counts changes decisions.
3. Add distinct trap, mixed, and style-switching opponents and compare candidates against the same deals. Confirm any selected change with the official judge, fresh servers and independent seeds, and actual entrants when available.
