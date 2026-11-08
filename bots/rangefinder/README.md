# Rangefinder

Rangefinder keeps M5 Counterplay's postflop thresholds as its base (using a 16-sample
equity budget for timing) and adds a narrowly scoped opponent model: it stores
the opponent's five private cards only after a showdown, then
uses those revealed hands to estimate the opponent's range for a similar public
action profile. Known cards are removed from that range. The estimate is mixed
with the uniform legal-hand prior using `n / (n + 8)`, where `n` is the
similarity-weighted number of revealed hands. Rangefinder changes postflop call/fold
decisions only when at least 3.5 weighted observations support the estimate;
otherwise M5 acts unchanged.

This is a compact online range learner for the challenge's one-opponent,
one-half setting, not a claim to reproduce a full Bayesian poker solver. It
uses the official `omaha_score` evaluator and keeps all learned data in the
per-half memory object. Its central hypothesis is that revealed holdings from
similar lines can improve on a uniform random-opponent equity estimate, while
confidence shrinkage limits damage from sparse or biased showdown samples.

## Run

```sh
python3 league/run.py --bot rangefinder --zoo all --seeds 3
python3 league/run.py --bot rangefinder --opp m1_equity,m2_cfr,m3_exploit,m4_learned,m5_challenger,m5_counterplay --seeds 3
```

Every run appends its rows to `league/results.csv`.

## Research basis

- Southey et al., [Bayes' Bluff: Opponent Modelling in Poker](https://poker.cs.ualberta.ca/publications/UAI05.pdf), models uncertainty about game state separately from uncertainty about opponent strategy. Rangefinder applies that separation to showdown-revealed holdings and uses explicit shrinkage because the available sample is small.
- Johanson et al., [Evaluating Robustness of Localized Opponent-Model-Based Strategies in Poker](https://poker.cs.ualberta.ca/publications/NIPS07-rnash.pdf), show why a narrowly optimized counterstrategy can be brittle when its opponent model is wrong. Rangefinder therefore falls back to M5 when range evidence is weak and caps the empirical range's influence through a prior.
- The challenge guide defines heads-up Short Deck 5-Card Pot-Limit Omaha: a 36-card deck, five private cards, exactly two private plus three board cards, 80-chip stacks, and a one-second action cap. Rangefinder respects these constraints by calling the repository evaluator and using bounded Monte Carlo sampling.

## Known limitation

Showdown hands are a selected sample: hands that folded are never revealed, and
the sample count is small within a single half. The prior mixture and evidence
threshold reduce this bias but do not eliminate it. Performance must be judged
over held-out duplicate-deal seeds and against the full local roster before
considering promotion.
