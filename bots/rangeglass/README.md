# Rangeglass

Rangefinder-derived research candidate. It stores only showdown-revealed hands,
weights them by public action profile, removes blockers, samples equity against
the observed range, then shrinks once toward the random-hand prior. The single
shrink avoids double-counting the same prior. M5 preflop play is unchanged, but
the postflop baseline also uses 16 rather than M5's 48 samples, so this is not a
pure range-only ablation. This tests the combined speed/estimator change against
Anchor/pressure policies; showdown-selection bias remains a limitation.
