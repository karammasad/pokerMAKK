# Research-backed poker bot roadmap

## What “best” means here

There is no defensible way to promise an “absolute” winner against unknown submissions. The game is an imperfect-information, zero-sum problem, and our opponent population is only a proxy for the tournament field. The practical target is a bot that is hard to exploit, never forfeits, wins consistently against weaker styles, and has measured evidence for each change.

`m5_challenger` is the selected default policy as of November 7, 2026. In fresh-server official-judge matches it beat `equity_guarded` by +0.362 bb/deal over 10,000 paired deals (95% CI [+0.205, +0.518]), and won all 12 matches against the four starter baselines (three 1,000-deal seeds each), with zero errors/timeouts. Keep `equity_guarded` and `m1_equity` as comparison fallbacks; the `POKER_BOT` environment variable can select any tested entry. Method 2 remains a coarse one-street warm start; Method 4's learned model is rejected because held-out MAE is still too high.

## Architecture to build toward

1. **Verified game model and estimator.** Keep `game.py` and `evaluator.py` authoritative. Generate equity labels with `evaluator.omaha_score`; encode exact two-hole/three-board Omaha usage, suit-isomorphic cards, pot odds, position, stacks, and future-card potential.
2. **Robust strategy backbone.** Replace the toy Method 2 payoff table with external-sampling MCCFR/CFR+ over the full sequential betting game. The action tree is exact because the game supplies four actions and raise sizes. Abstract cards by distributions over future hand strength/potential, then solve offline and ship a compact average strategy.
3. **Bounded opponent adaptation.** Keep `m5_challenger` as the default while it holds its measured edge. Estimate opponent ranges/tendencies with Bayesian shrinkage, and mix toward a best response only as the evidence grows. Add a stop-loss or uncertainty trigger that returns to the base strategy.
4. **Learned equity only as a measured replacement.** Train on independently generated state groups, not neighboring samples from the same exact deal. Predict mean and uncertainty (and eventually future potential), check calibration by street and texture, then require held-out MAE below 0.02, inference below 0.1 ms, and no league regression before activation.
5. **Population improvement last.** Build an empirical payoff matrix across the zoo, snapshots, and varied opponent policies. Run PSRO-style best responses only after the candidate pool has enough reliable payoff data. Evaluate the chosen mixture on unseen seeds.

## Research that informs those choices

- [Zinkevich et al., “Regret Minimization in Games with Incomplete Information,” NeurIPS 2007](https://papers.nips.cc/paper_files/paper/2007/hash/08d98638c6fcd194a4b1e6992063e944-Abstract.html) introduces counterfactual regret minimization and establishes why minimizing regret at information sets supports equilibrium computation.
- [Lanctot et al., “Monte Carlo Sampling for Regret Minimization in Extensive Games,” NeurIPS 2009](https://papers.nips.cc/paper/2009/file/00411460f7c92d2124a67ea0f4cb5f85-Paper.pdf) gives external- and outcome-sampling MCCFR, including regret guarantees. This is the right family for offline training under limited compute; the current small matrix trainer is only a scaffold.
- [Ganzfried & Sandholm, “Potential-Aware Imperfect-Recall Abstraction with Earth Mover’s Distance,” AAAI 2014](https://www.cs.cmu.edu/~sandholm/potential-aware_imperfect-recall.aaai14.pdf) supports bucketing by future-strength distributions rather than current mean equity alone. That matters in Omaha, where redraws and suit/board structure can change hand value sharply.
- [Bowling et al., “Heads-up Limit Hold’em Poker Is Solved,” Science 2015](https://webdocs.cs.ualberta.ca/~games/poker/publications/heads-up_limit_poker_is_solved.acm2017.pdf) shows the value of CFR+ at scale. Its result is for limit Hold’em, so we borrow methods, not its strategy or solved status.
- [Moravčík et al., “DeepStack: Expert-Level Artificial Intelligence in Heads-Up No-Limit Poker,” Science 2017](https://arxiv.org/abs/1701.01724) motivates continual re-solving and learned value estimates. Our one-second action deadline and CPU-only runtime favor offline strategy tables first.
- [Brown & Sandholm, “Superhuman AI for Heads-Up No-Limit Poker: Libratus Beats Top Professionals,” Science 2018](https://noambrown.github.io/papers/17-Science-Superhuman.pdf) motivates a robust equilibrium core, endgame reasoning, and systematic strategy repair rather than hand-written bluff rules.
- [Burch et al., “AIVAT: A New Variance Reduction Technique for Agent Evaluation in Imperfect Information Games,” AAAI 2018](https://ojs.aaai.org/index.php/AAAI/article/view/11481) is a later evaluation improvement. We should first use paired duplicate seeds; add AIVAT only with a frozen, independently trained value estimator to avoid evaluation leakage.
- [Lanctot et al., “A Unified Game-Theoretic Approach to Multiagent Reinforcement Learning,” NeurIPS 2017](https://proceedings.neurips.cc/paper/2017/hash/3323fe11e9595c09af38fe67567a9394-Abstract.html) motivates PSRO and a diverse opponent population. It also warns against overfitting to a small fixed set of opponents.
- [Southey et al., “Bayes' Bluff: Opponent Modelling in Poker,” UAI 2005](https://webdocs.cs.ualberta.ca/~bowling/papers/05uai.pdf) motivates Bayesian opponent models that represent uncertainty over behavior and update as actions are observed. Our `bayes_ev` prototype uses a much smaller Dirichlet-smoothed fold/call/raise response model; it is an experiment, not a reproduction of their method.

## Work order

1. Land the evaluator/game invariants and fixed observation corpus in `tests/`.
2. Use the HTTP parity test and fresh-server match runner to establish a reproducible tournament baseline.
3. Implement and validate real MCCFR+ traversals and information-set indexing; compare abstraction sizes and report exploitability proxies.
4. Extend the zoo with threshold variants, style switchers, traps, and saved versions of our own bots.
5. Replace the equity model only after the separate validation gate passes.
6. Build paired payoff comparisons and PSRO after all candidate rows exist.
7. Re-run all official checks and freeze the tested SHA before submission.

## Candidate portfolio (November 2026)

`bots/portfolio.py` adds six explicit comparison policies: the current equity core, a guarded value policy, a pressure policy with a low river bluff frequency, a higher-sample equity version, a bounded Bayesian action-frequency adapter, and `bayes_ev`, which estimates opponent fold/call/raise responses after our bets and compares their shrunk expected value with checking. These are controlled experiments around the same evaluator/equity backbone, not solved poker agents. The official HTTP runner can select a candidate with `--bot` and an opposing local strategy with `--opponent-bot`.

The 57-match `bayes_ev` screen (three paired seeds × 200 deals against 19 practice, baseline, and portfolio opponents) averaged +4.070 bb/deal overall and made no errors or fallbacks. It averaged +1.00 bb/deal against the nine toy styles, but lost on all three seeds to `m1_equity` (−1.728 bb/deal) and `equity_guarded` (−2.462 bb/deal). Against the newly added `m5_challenger`, its three-seed mean was −1.478 bb/deal. Keep it as a benchmark and do not promote it. Raw results are in [`league/benchmarks/bayes_ev_screen.csv`](league/benchmarks/bayes_ev_screen.csv). The large overall mean is dominated by weak toy opponents and is not a measure of tournament strength.

### Next research challengers

`m6_safeadapt` keeps M5 as its anchor and uses a posterior lower bound to suppress weak river bluffs only when observed responses make them look unprofitable; it also adjusts marginal calls after sustained aggression. This is a small adaptation experiment inspired by [SafeAdapt-Poker](https://arxiv.org/abs/2610.20473), not a reproduction. It lost to M5 by 0.221 bb/deal on five 1,000-deal paired seeds.

`m7_precision` uses 32 equity samples normally and refines to 96 near an action threshold, while preserving M5's decisions. It gained +0.291 bb/deal against M5 in a 10,000-deal in-process screen, but the independent fresh-server holdout was only +0.049 bb/deal (95% CI [−0.096, +0.194]). Keep it in the pool; evidence does not justify promotion yet. Raw screens are in [`league/benchmarks/m7_precision_screen.csv`](league/benchmarks/m7_precision_screen.csv), with official rows in `league/results.csv`.

`m8_bayes_types` maintains a recent-window Bayesian posterior over four public-action behavior types, following the strategy-posterior idea in [Bayes' Bluff](https://arxiv.org/abs/1207.1411). Its hand-coded likelihoods are an explicit abstraction. It lost to M5 by 0.041 bb/deal on 10,000 in-process paired deals (95% CI [−0.069, −0.012]); keep it as a comparison policy.

`m9_cfrplus` is a separate 20,000-iteration external-sampling MCCFR+ strategy with an M5 fallback. It lost to M5 by 3.088 bb/deal on 10,000 paired deals (95% CI [−3.431, −2.745]); a 50-visit fallback cutoff improved the five-seed tuning mean to −1.087 bb/deal, then lost by −0.826 bb/deal on five separate holdout seeds (95% CI [−1.220, −0.433]). The table is gzip-compressed at `bots/m9_cfrplus/tables/strategy.json.gz` and kept as a negative research result.

`m10_seq_cfr` trains the same CFR+ traversal for 10,000 iterations while preserving the ordered public action sequence in each information key. It lost to M5 by 4.291 bb/deal on 10,000 paired deals (95% CI [−4.646, −3.935]). This indicates that action-order preservation alone does not repair the current card abstraction or training setup. The 145,580-infoset table is kept as a reproducible comparison, not an adoption candidate.

The candidate pool in `league/run.py` includes M6–M10 so `--opp all` compares future models against the full research set. CFR+ has strong poker results in solved or much smaller abstractions, but these local imperfect-recall policies do not inherit those guarantees.

The repo also has an external-sampling MCCFR+ trainer over the official sequential betting game. It uses an explicit imperfect-recall abstraction, so full-game MCCFR convergence guarantees do not transfer to this prototype. Its 5,000-iteration policy covered 121,306 infosets (about 13 MB) and lost to `m1_equity` on three held-out 200-deal seeds, averaging **−5.47 bb/deal**. It remains research-only.

### Tournament evidence to date

- A 200-deal screen across three seeds and 18 practice/incumbent/candidate opponents ranked `equity_pressure` first by average points, but longer head-to-head tests overturned that ranking. On 10 fresh-server matches × 1,000 duplicate deals against `m1_equity`, it lost 9 and chopped 1: **−0.721 bb/deal**, 95% CI **[−0.869, −0.572]**, zero errors.
- `equity_guarded` won all 10 fresh-server 1,000-deal duplicate matches against `m1_equity`: **+0.901 bb/deal**, 95% CI **[+0.759, +1.043]**, zero errors, maximum half think time 1.151 seconds.
- It also won all 12 official fresh-server matches against the four starter baselines and all 27 in-process 1,000-deal runs against the nine-style practice zoo, with zero errors/fallbacks. These are baseline/zoo results; no submitted team bots were available.
