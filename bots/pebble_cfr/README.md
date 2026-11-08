# PebbleCFR

Sequence-aware external-sampling MCCFR+ prototype trained with the repo's exact
game transitions and terminal evaluator, using an imperfect-recall equity
abstraction and M5 Counterplay fallback for states with fewer than three visits.

The committed table was generated with:

```sh
python3 -m bots.mccfr.train.solver --iterations 1000 --node-limit 300 \
  --history-abstraction sequence --seed pebble-cfr-2026-11-07 \
  --out bots/pebble_cfr/tables/strategy.json
```

This is a low-budget feasibility prototype, not an equilibrium or tournament
strength claim. Training time, visited states, coverage, table size, and held-
out league results must be checked before increasing the budget.
