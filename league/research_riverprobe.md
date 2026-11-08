# Poker research and river-probe experiment

## Context and sources

- Brown and Sandholm, [Libratus: The Superhuman AI for No-Limit Poker](https://ijcai.org/proceedings/2017/772), uses an approximate equilibrium blueprint, nested subgame solving, and self-improvement. This is a heads-up no-limit Hold'em system, not a ready-made solution for short-deck PLO5 or this bot's time budget.
- Brown and Sandholm, [Safe and Nested Subgame Solving for Imperfect-Information Games](https://arxiv.org/abs/1705.02955), explain why the opponent's alternatives outside the currently reached subgame matter; a locally optimal response can be globally exploitable. Correct safe re-solving requires a blueprint, opponent counterfactual values and a subgame solver. The experiment below has none of those and carries no such guarantee.
- Ge et al., [Safe and Robust Subgame Exploitation in Imperfect Information Games](https://proceedings.mlr.press/v235/ge24b.html), study reducing vulnerability to incorrect opponent models. Their OX-Search guarantee depends on their actual method, which is not implemented here. It motivates investigating evidence-gated deviations and evaluating them against multiple opponent types, not claiming that those heuristics are safe.
- Brown et al., [Combining Deep Reinforcement Learning and Search for Imperfect-Information Games (ReBeL)](https://arxiv.org/abs/2007.13544), combine self-play and search over public beliefs. A real implementation would need a trained value model and game-specific validation; neither is supplied by a simple random-equity sampler.

- [StratFormer](https://arxiv.org/abs/2604.25796) (2026 preprint) explores learned opponent adaptation in Leduc Hold’em. Its small-game results are exploratory context, not validation for this PLO5 implementation or its compute budget.

## Experiment: `messi_riverprobe`

Start from the promoted v7 policy. Track responses to our river bets in per-half memory; once at least 12 observations indicate a high fold rate, occasionally add a half-pot bluff when the existing action is to check, the bet costs at most 60% of the pot, and our random-hand equity estimate is low. A half-pot pure bluff has a one-third break-even fold rate if a call always loses and reraises are ignored; the 65% gate is a deliberately conservative heuristic, not an estimate of true expected value.

Caveats: existing river bets are selected by our hand strength, responses to them need not match responses to extra bluffs, estimates are correlated across hands, and the random-equity estimate is not range-aware. The empirical gate uses a smoothed point estimate, not a confidence bound. V7's existing reraise counter is also censored. Performance against a named bot is not evidence of equilibrium or robustness against arbitrary opponents.

Registration: `league/run.py` and `BOT_CATALOG.md`; tests: `tests/test_messi_riverprobe.py`. Initial screen uses 1000 duplicate deals per seed against v7, v2, v6, Messi and m5, seeds 32000–32002. Runs append to `league/results.csv`. Any promotion requires an independently significant 8–10+ seed pooled win against current default v7 and a clean full zoo gate; a screening win alone is insufficient.

## Initial screen (seeds 32000–32002)

Each result pools 3000 paired deals, with CI reconstructed from the per-seed `match` variances including between-seed differences. All 15 matches had zero errors and fallbacks.

| Opponent | bb/deal | 95% CI | Verdict |
| --- | ---: | --- | --- |
| `messi_v7` | +0.0083 | [-0.0137, +0.0303] | chop |
| `messi_v2` | -0.0340 | [-0.1016, +0.0336] | chop |
| `messi_v6` | +0.4127 | [+0.2285, +0.5969] | win |
| `messi` | -0.0240 | [-0.1054, +0.0574] | chop |
| `m5_challenger` | -0.1170 | [-0.2880, +0.0540] | chop |

The full three-seed zoo gate completed 231 matches: 163 wins, 67 chops, 1 loss, zero errors and fallbacks, and a maximum 2.403 seconds of thinking per half.

This is an initial screen only. The probe did not establish an edge against v7 and should not replace it. In particular, a confidence interval spanning zero is not proof of no disadvantage. A subsequent independent study would require more seeds, alternative adversarial opponents, and direct analysis of action differences.

## Next investigation

V7 calls `_fast_action` for postflop decisions once accumulated thinking time reaches 1.5 seconds. Its reraise-fold rule is below that early return, so the defensive threshold is not applied in the fast path. A promising next test is a separately registered policy with a low-cost, consistent fast-path response, measured across the full half, not only early decisions. This is a hypothesis, not evidence that enforcing the threshold helps: v6-style strict folding was exploitable, and response tracking and sampling costs can erase any benefit. Compare response frequencies, action changes, runtime, and pooled results on unseen seeds before considering promotion.
