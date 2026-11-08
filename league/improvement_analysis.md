# How to improve the tournament bot: evidence-led analysis

Date: 2026-11-08. Current entry default: `messi_v7`.

## Executive recommendation

Keep v7 as the current champion while broadening the search. Do not choose between “improve Messi” and “improve Aguero” as if these were the only two options. First improve the model of hidden cards and the quality of our experiments; then test targeted changes borrowed from other policies. A selector or hybrid is a later experiment, and should only be built around a measured condition where the alternate policy actually wins.

The current evidence does **not** show that Aguero/Atlas is a better base than v7. In the three-seed focused screen with seeds 34000–34002, Atlas averaged −0.298 bb/deal vs v7 (per-seed: +0.102, −0.406, −0.590); Atlas Learning averaged −0.163 ( +0.173, −0.417, −0.246). Both also averaged negative against v2. These are small screens, not final strength estimates. The run was inadvertently started twice; duplicate-seed records are present in the append-only CSV, so do not count duplicate rows as independent samples. The consistency of direction is enough to deprioritize a full Atlas zoo run, not enough to establish a population-level loss.

V7 has stronger evidence: ten seeds vs v6 yielded +0.1763 bb/deal, CI [+0.0775, +0.2751], and its three-seed zoo gate had 153 wins, 75 chops, no losses, zero errors or fallbacks. V2 led the focused three-seed table on average bb/deal and beat v6 in a separate ten-seed check (+0.3015, CI [+0.1855, +0.4175]); however, v7 vs v2 was a ten-seed chop (+0.0350, CI [−0.0037, +0.0737]). This is a frontier of near-tied, non-transitive policies, not a solved best bot. V7 beat Aguero by +2.3177 bb/deal in the focused pooled table, so copying Aguero wholesale is especially hard to justify.

## What the current strategies actually model

`messi_v7` has three response mechanisms layered on `messi_v2`: a response-gated turn/river semi-bluff; a small preflop open mix; and a postflop reraise threshold that falls from 0.85 to 0.70 or 0.55 as observed reraise frequency rises. Its observations are incomplete: `_track_reraise_frequency` resolves a street only when a later decision exposes the opponent's action, and can miss terminal responses and calls that end the street. Its 1.5-second pace guard also switches to `_fast_action`, which does not use the adaptive reraise threshold. The read is therefore both censored and action-path dependent.

`aguero` adds cross-hand fold-to-bet rates, preflop folds, overall aggression, and showdown strength reads. These are useful signals, but are coarse. Showdowns are selected: the bot only learns private cards when a hand reaches showdown. Aggregate fold counts can mix very different hand strengths, board textures, positions, and bet sizes. It also inherits a 0.85 reraise rule. `atlas` adds a richer action-response ledger and conservative beta bounds over street, size, and whether a bet faces aggression, at the cost of more code and computation. The focused evidence so far does not show that this extra model wins against v7.

`messi_riverprobe` and `messi_bayes` changed one narrow response threshold or bluff decision. Both chopped against v7 on three seeds. The river probe's fold statistic is conditioned on the baseline's selected bets and therefore does not directly estimate the opponent's response to an added bluff. The Bayesian variant smooths the frequency but inherits the same censored observations. Smoothing a biased count does not remove the bias.

## Largest strategic opportunity: estimate equity against a range

`bots/common/equity.py` samples the opponent's five cards uniformly from unseen cards and scores the exact Omaha hand evaluator. That is a useful, fast baseline for a truly random opponent, but after a raise, call, or check, real opponents' hands are not uniformly random. The evaluator may be exact while the *range assumption* is wrong. This likely matters more than another small adjustment to a fixed equity threshold: it changes calls, folds, value bets, and bluff decisions together.

The smallest credible range-aware step is not a transformer. Build an auditable Bayesian range model over precomputed five-card hand-strength buckets, conditioned on public context: preflop action, street, position, bet size relative to pot, and whether the action is a raise or call. Use showdown hands to update likelihoods and keep non-showdown action likelihoods trained from self-play or the bot zoo. At decision time, sample candidate opponent holdings with posterior weights, reject card collisions, and estimate equity with `evaluator.omaha_score`. Include a uniform-range fallback and shrink sparse buckets toward it. Cache keys must include board, hero cards, context, and a versioned range summary; do not reuse the current uniform-equity cache key for a different range.

Evaluate calibration as well as win rate: bucket predictions into equity deciles and compare predicted showdown equity with revealed outcomes, separated by action context. A model that improves calibration but not match results is not ready to promote; a model that wins only against the archetype used to train it may be overfit.

## Recommended build order

1. **Repair measurement first.** Build a small analysis utility that deduplicates identical match reruns for analysis without changing or deleting append-only raw rows. Tag experiments with a unique run identifier in a sidecar under `/tmp` or a new ledger column only if schema migration is deliberate. Run each process once. Use fresh held-out seeds and avoid concurrent CPU-heavy matches when evaluating pace-sensitive bots.
2. **Instrument decisions, not just outcomes.** On a fixed corpus of legal states, compare v7 to candidates: record action changes, street, pot odds, estimated equity, sample budget, opponent action context, memory counters, and elapsed time. This shows whether a proposed model actually changes the target decisions and whether a gain comes from more calls, fewer bluffs, or timing fallback.
3. **Fix response accounting.** Use one pending record per our bet/raise, resolved on the opponent's next action or at hand end. Record fold/call/raise and size, street, position, and whether we were facing aggression. Never count a call at showdown as a fold or silently omit terminal folds. Keep these counters per-half in `memory`.
4. **Add weighted ranges.** Start with a compact hand-strength bucket table and a small number of action-context buckets. Generate training observations from self-play across the distinct policy families (v7, v2, Aguero/Atlas, and a few structurally different bots), while holding out entire policies and seeds. This guards against a model that only recognizes its training opponents.
5. **Test one decision family at a time.** First calls facing a postflop raise (where v7's response counter acts), then river bluff/value decisions, then preflop response ranges. Keep all unrelated thresholds fixed. Use paired deals and preserve both seat assignments.
6. **Only then test a selector.** A whole-policy switch should use a clear, low-cost, opponent signal and switch at a stable boundary (for example after a fixed initial hand sample), with policy memories separated. Do not call both full policies on every action: it doubles compute and may change time-guard behavior. Prefer a small action-level adjustment using a calibrated range posterior before trying a policy-level switch.

## Tournament protocol for each candidate

Use development seeds to select features and thresholds, then freeze code and parameters. Confirm on fresh seeds with 1,000 duplicate deals per seed, both halves, paired bb/deal and 95% CI. Compare the candidate with v7, v2, m5_challenger, and the best distinct-family challenger that survives screening. Require a positive pooled CI against v7 across at least 8–10 fresh seeds before calling it a promotion candidate. Run the three-seed full zoo only after it has a credible focused edge; this avoids spending a long gate on variants that already chop or lose to v7. Preserve all rows and label screens, development, and confirmation separately.

Because the default's decision path depends on accumulated wall time, report max and mean half time, p50/p99 decision latency, and fallback counts. Reject a nominal strength gain if it depends on timing artifacts, exceeds the four-second per-half target, or creates any illegal action/fallback.

## Research that informs this plan

- Brown and Sandholm, [Safe and Nested Subgame Solving for Imperfect-Information Games](https://arxiv.org/abs/1705.02955): a poker subgame cannot be optimized in isolation from the rest of the strategy; safe solving uses a whole-game blueprint and opponent counterfactual values. This repository does not currently have those ingredients, so a threshold heuristic must not be described as safe subgame solving.
- Brown et al., [Combining Deep Reinforcement Learning and Search for Imperfect-Information Games (ReBeL)](https://arxiv.org/abs/2007.13544): combines public-belief search with self-play learning. The transferable lesson is to model beliefs/ranges, not merely classify an opponent as “aggressive.” The trained value model and search are beyond the current 2 ms average budget without substantial precomputation.
- Ge et al., [Safe and Robust Subgame Exploitation in Imperfect Information Games](https://proceedings.mlr.press/v235/ge24b.html): formal safety under an inaccurate opponent model requires a defined method and assumptions. The project’s beta counters are not OX-Search and have no comparable guarantee.
- Caen et al., [StratFormer](https://arxiv.org/abs/2604.25796), accepted at Computers and Games 2026: opponent modeling plus a regularized shift from baseline toward best response, evaluated on Leduc Hold’em. This is recent and relevant to the selector idea, but Leduc's six cards and two rounds are far simpler than short-deck PLO5. Treat it as a design reference, not a performance prediction.

## Decision today

Keep `messi_v7` active. Do not spend a full evaluation on Aguero or Atlas unchanged. The next high-value research task is a correctly accounted, compact range model and fixed-state action-difference analysis. After that produces a specific, measurable improvement hypothesis, test a targeted v7 graft on fresh paired seeds. Only create a selector if evidence identifies a context where another policy wins and the signal can be observed cheaply and reliably.
