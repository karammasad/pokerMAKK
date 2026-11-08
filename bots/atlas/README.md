# Atlas

Research challenger built from the exact Aguero/City tournament snapshot at
`7d004f6`. Select with `POKER_BOT=atlas` or `python league/run.py --bot atlas`.
This frozen policy remains runnable independently of the selected entry in
`bots/active.py`; incumbent implementations are preserved.

## Design

- Correctly count fold/call/raise responses, including terminal folds and final
  calls that never appear in another decision observation.
- Separate streets, raise sizes, and ordinary bets from reraises. All observed
  data, sampling prefixes and random generators live in per-half memory.
- Shrink fold frequencies with a Beta prior. Approximate posterior bounds gate
  additional pressure; these are heuristic risk controls, not guaranteed
  confidence coverage or a solved poker strategy.
- Defend against repeated reraises and only add bluff reraises when evidence
  supports their actual cost relative to folding.
- Reuse Monte Carlo prefixes when refining estimates, and evaluate our river
  hand once per board. All scoring uses `evaluator.omaha_score`. Prefixes match
  the original deterministic uniform-range sampler exactly at equal sample
  counts. The policy's time guards can still change decisions with machine load.
- Charge hand-end work to the bot's internal timing budget. The shared wrapper
  ordinarily counts decisions only. Additional audit runs time both players'
  callbacks and check for exceptions hidden by the shared safety wrapper.

## Research basis and limits

[Computing Robust Counter-Strategies (2007)](https://poker.cs.ualberta.ca/publications/NIPS07-rnash.pdf)
and [Data Biased Robust Counter Strategies (2009)](https://proceedings.mlr.press/v5/johanson09a/johanson09a.pdf)
motivate retaining a baseline under uncertainty and trusting local observations
more as evidence accumulates. Atlas does not solve their modified games and
inherits no equilibrium or exploitability guarantee.

[Bayes' Bluff (2005)](https://poker.cs.ualberta.ca/publications/UAI05.pdf)
motivates opponent-strategy uncertainty and careful treatment of hidden hands.
Showdown-only strength estimates inherited from Aguero are selected samples;
they are not calibrated posterior opponent ranges. Equity remains against a
uniform random hand. No paper supplies validated numerical thresholds for this
specific Short Deck five-card Omaha game.

## Evaluation

Development uses seeds 12000–12001, 1000 duplicate deals per seed. These are
reused for iteration and cannot justify a held-out improvement claim. Prototype
versions and failed/contaminated runs are retained in the append-only ledger
with their version notes in `league/results_notes.md`.

Fresh confirmation and the required full-zoo/test-suite results are recorded
separately after freezing the final candidate. The historical tournament wrote
literal zero timing/fallback placeholders; its standings alone are not proof
that either side respected the timing budget.
