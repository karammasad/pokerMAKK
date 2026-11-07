# League results audit notes

`results.csv` is append-only as required by the project rules.

The first HTTP batch wrote rows 5–13 using a stale `RandomBot` process that was still bound to port 5009. Those nine rows are mislabeled as `calling_station`, `always_half`, and `always_pot`; disregard them. The corrected full HTTP rerun follows those rows and verified each opponent's `/` endpoint name before playing. The first three rows (`random`, seeds 0–2) were valid.

The first corrected full-zoo league stored `think_s` as the sum across both duplicate halves. In the targeted timing rerun rows later in `results.csv`, `think_s` is the slower half; the run output printed each half separately.

The results after the targeted timing rows include the current 12,000-state test-corpus runs for Methods 2–4 and the latest fresh-server official HTTP validation for Method 1 (four baselines, seeds 7–9). `tools/run_datathon_match.py` appends future fresh-server match summaries automatically.
