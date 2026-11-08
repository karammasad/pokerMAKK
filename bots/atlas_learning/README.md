# Atlas learning candidate

An outcome-based risk layer over frozen Atlas (`2d9d249`), evaluated as the
separate ID `atlas_learning`. It never changes frozen Atlas's implementation.

For marginal terminal river calls, the hand ends immediately after a
call. The actual showdown share minus the call's pot price is an observable
comparison with folding. A bounded 32-observation window in coarse price and ordinary-bet versus reraise
contexts estimates whether these calls are losing. At least 8 calls and a
conservative posterior upper estimate are required before suppressing a call.
Strong-value calls remain available. One in eight blocked opportunities can
probe again only at a limited call cost, and only if original Atlas would call.
All counters and outcomes reset per half. The bot writes no runtime files.

This is adaptation to sampled outcomes, not proof of guaranteed improvement.
Calls that were folded supply no invented outcome label. Observed calls are a
selected sample; coarse context aggregation and a changing opponent still
limit the model. Probe limits bound additional exploration but do not bound
whole-game exploitability. A fresh validation must decide whether this layer
improves the real roster.

For a repeatable offline agent improvement loop:

```sh
python league/improve.py --baseline atlas --candidate atlas_learning \
  --seed-start 12020 --seeds 3 --out /tmp/atlas-improvement.json
```

The runner alternates execution order, audits both players' callbacks, records
every match in the append-only league ledgers, clusters comparison uncertainty
by deal seed, ranks weak matchups, and rejects candidates with dirty execution
or no credible improvement. Recommendations use development data and require
a separately frozen fresh-seed confirmation. It never edits code, silently
changes the default, or starts a recurring background job.


The first revised candidate showed a positive fixed fresh-seed gain over frozen
Atlas. The initial strict all-opponent timing gate remained false because an
Anchor control half exceeded 4s; the row and paired timing recheck are retained.
A separately disclosed analysis across Aguero, Messi, Mahrez and Ederson has
80 timing-clean records (40 matched comparisons), mean gain +0.054275 bb/deal,
seed-cluster t95 [+0.026521,+0.082029]. This narrower scope does not erase the
Anchor timing failure. Published as an opt-in challenger. The Atlas development checkout passed
127 tests (1 optional skip); its final full-zoo check is in progress.
The current main entry default remains the teammate-promoted Messi v6.

The improvement evaluator supports enforced confirmation protocols:

```sh
python league/improve.py --baseline atlas --candidate atlas_learning \
  --seed-start 12030 --seeds 3 --out /tmp/atlas-next-development.json
python league/improve.py --baseline atlas --candidate atlas_learning \
  --seed-start 44000 --seeds 10 --phase confirmation \
  --development-report /tmp/atlas-next-development.json --out /tmp/next-confirmation.json
```

Development and confirmation must use identical frozen bot assets; select a
new development report if assets or routing changed. The improvement runner records both players' callback errors, mean/max
decision times and callback-plus-decision compute envelopes in its JSON report.
The instrumented full-zoo development run is separate from this publication.
