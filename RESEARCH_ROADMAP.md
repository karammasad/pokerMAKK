# Research-backed poker bot roadmap

## What “best” means here

There is no defensible way to promise an “absolute” winner against unknown submissions. The game is an imperfect-information, zero-sum problem, and our opponent population is only a proxy for the tournament field. The practical target is a bot that is hard to exploit, never forfeits, wins consistently against weaker styles, and has measured evidence for each change.

`m1_equity` is the incumbent reference. `equity_guarded` now passes same-seed head-to-head adoption checks and is selected as the default policy; keep `m1_equity` available as the comparison fallback. Method 2 remains a coarse one-street warm start; Method 4's learned model is rejected because held-out MAE is still too high.

## Architecture to build toward

1. **Verified game model and estimator.** Keep `game.py` and `evaluator.py` authoritative. Generate equity labels with `evaluator.omaha_score`; encode exact two-hole/three-board Omaha usage, suit-isomorphic cards, pot odds, position, stacks, and future-card potential.
2. **Robust strategy backbone.** Replace the toy Method 2 payoff table with external-sampling MCCFR/CFR+ over the full sequential betting game. The action tree is exact because the game supplies four actions and raise sizes. Abstract cards by distributions over future hand strength/potential, then solve offline and ship a compact average strategy.
3. **Bounded opponent adaptation.** Keep `equity_guarded` or a validated CFR strategy as the default. Estimate opponent ranges/tendencies with Bayesian shrinkage, and mix toward a best response only as the evidence grows. Add a stop-loss or uncertainty trigger that returns to the base strategy.
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

## Work order

1. Land the evaluator/game invariants and fixed observation corpus in `tests/`.
2. Use the HTTP parity test and fresh-server match runner to establish a reproducible tournament baseline.
3. Implement and validate real MCCFR+ traversals and information-set indexing; compare abstraction sizes and report exploitability proxies.
4. Extend the zoo with threshold variants, style switchers, traps, and saved versions of our own bots.
5. Replace the equity model only after the separate validation gate passes.
6. Build paired payoff comparisons and PSRO after all candidate rows exist.
7. Re-run all official checks and freeze the tested SHA before submission.

## Candidate portfolio (November 2026)

`bots/portfolio.py` adds five explicit comparison policies: the current equity core, a guarded value policy, a pressure policy with a low river bluff frequency, a higher-sample equity version, and a bounded Bayesian action-frequency adapter. They are controlled ablations around the same evaluator/equity backbone. The official HTTP runner can select a candidate with `--bot` and an opposing local strategy with `--opponent-bot`.

The repo also has an external-sampling MCCFR+ trainer over the official sequential betting game. It uses an explicit imperfect-recall abstraction, so full-game MCCFR convergence guarantees do not transfer to this prototype. Its 5,000-iteration policy covered 121,306 infosets (about 13 MB) and lost to `m1_equity` on three held-out 200-deal seeds, averaging **−5.47 bb/deal**. It remains research-only.

### Tournament evidence to date

- A 200-deal screen across three seeds and 18 practice/incumbent/candidate opponents ranked `equity_pressure` first by average points, but longer head-to-head tests overturned that ranking. On 10 fresh-server matches × 1,000 duplicate deals against `m1_equity`, it lost 9 and chopped 1: **−0.721 bb/deal**, 95% CI **[−0.869, −0.572]**, zero errors.
- `equity_guarded` won all 10 fresh-server 1,000-deal duplicate matches against `m1_equity`: **+0.901 bb/deal**, 95% CI **[+0.759, +1.043]**, zero errors, maximum half think time 1.151 seconds.
- It also won all 12 official fresh-server matches against the four starter baselines and all 27 in-process 1,000-deal runs against the nine-style practice zoo, with zero errors/fallbacks. These are baseline/zoo results; no submitted team bots were available.
