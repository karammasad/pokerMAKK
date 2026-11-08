# Northstar development notes

Northstar is a Telltide-derived experiment, not a proven upgrade or a new default. It records the outcomes of its own large river calls that reach showdown, uses a smoothed win-rate estimate, and gates some calls only after 12 observations. It keeps one fifth of qualifying calls to retain a limited signal if the opponent changes. Showdowns are selected observations, and the bot may still be exploitable; this rule is not an equilibrium strategy.

## Why test it

Three seeds of 1,000 duplicate deals against Anchor and Kestrel were instrumented. Telltide's observed calls facing large river bets averaged approximately −8.9 bb relative to folding, in 72 and 71 instances respectively. This compares realized outcomes with a fold at the decision point; the samples are selected and the observation alone does not establish a profitable strategy change.

An always-fold diagnostic (`northstar_probe`) improved average results versus Telltide by approximately +0.16 bb/deal against Anchor and Kestrel on seeds 8300–8302. But against a synthetic opponent (`river_ruse`) which always pot-bets when checked to on the river, that probe averaged −0.193 bb/deal while Telltide averaged +0.360 on seeds 8400–8402. Thus the unconditional fold is not suitable as a promoted agent.

The gated version's fresh three-seed matched screen (seeds 8500–8502, 1,000 deals) produced mean changes versus Telltide: Anchor +0.052, Kestrel −0.009, Turnblade +0.031, Stones −0.002, Ederson +0.025, River Ruse −0.004 bb/deal. These are small point estimates, not proof of improvement. Runtime-dependent sampling can also change actions across runs. Full-roster and independent holdout evaluation are needed.

The raw league rows are appended to `league/results.csv`; see `league/results_notes.md` for run details. River Ruse is a sparring bot, not a claim about a teammate's strategy.
