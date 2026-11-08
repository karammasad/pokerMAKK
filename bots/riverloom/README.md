# Riverloom

Sequential Monte Carlo candidate. It starts at 16 equity samples and
re-estimates at 32 or 64 samples only when uncertainty overlaps a call/raise
threshold, subject to cumulative think-time guards. It uses the same action
thresholds and preflop policy as M5 Counterplay. This tests whether sampling
effort is more useful near decisions than a fixed budget.
