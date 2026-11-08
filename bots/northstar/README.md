# Northstar

Experimental Telltide variant: tracks outcomes of its own large river calls at showdown. After 12 such showdowns, a smoothed win rate below 30% gates some folds; approximately one fifth of qualifying calls remain, selected using private cards, to detect opponent changes. A late-half guard reduces samples when facing a bet to protect the timing budget. This is a heuristic with selected showdown data, not an equilibrium guarantee.

Before the pace and exploration changes, in matched 1,000-deal tests on seeds 8500–8502, average bb/deal changes versus Telltide were +0.052 against Anchor, −0.009 against Kestrel, +0.031 against Turnblade, −0.002 against Stones, +0.025 against Ederson, and −0.004 against River Ruse. These small differences are not proof of an edge.

An initial full-roster run was stopped after 104 rows because one half used 4.139 seconds, above this repository’s 4-second target. A revised version with the late-half guard completed focused 1,000-deal, three-seed checks against M8, Anchor, Kestrel, and River Ruse with no errors/fallbacks and maximum observed half time below 1.9 seconds. A fresh full-roster run remains required.
