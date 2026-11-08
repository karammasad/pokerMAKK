# Telltide

Bayesian bet-response EV candidate. It tracks fold/continue/raise responses to
our own half-pot and pot raises by street, uses priors until eight observations
exist, and compares the estimated raise EV with checking. All other decisions
fall through to M5 Counterplay. The model is deliberately local and shrunk;
evaluate calibration and paired chip EV before treating it as an exploit.
