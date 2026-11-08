"""Official-format round-robin tournament runner for the curated shortlist.

Runs every pairing at the true competition format (1000 deals x 2 halves,
duplicate deals, pooled bb/deal, 95% CI verdict), pools across several seeds
per pairing for a tighter confidence interval, appends every match to
league/results.csv (append-only), and writes league/leaderboard.md with
final standings.
"""
import csv
import itertools
import math
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import game
from bots.common.safe import wrap
from league.run import load_bot, play_half

SHORTLIST = [
    "m5_challenger", "m5_classic", "m5_counterplay", "kestrel", "osprey",
    "ederson", "mahrez", "telltide", "northstar", "m9_cfrplus", "aguero",
]

DEALS = 1000
SEEDS = (0, 1, 2)


def pooled_match(bot_name, opp_name, seeds=SEEDS, deals=DEALS):
    wrapped_bot = wrap(load_bot(bot_name))
    wrapped_opp = wrap(load_bot(opp_name))
    all_bb = []
    errors = 0
    t0 = time.perf_counter()
    for seed in seeds:
        halves = []
        for h in (1, 2):
            n, err, _ = play_half(wrapped_bot, wrapped_opp, seed, h, deals)
            halves.append(n)
            errors += err
        paired_bb = [(halves[0][i] + halves[1][i]) / game.BIG_BLIND for i in range(deals)]
        all_bb.extend(paired_bb)
    n = len(all_bb)
    mean = statistics.mean(all_bb) if all_bb else 0.0
    se = statistics.stdev(all_bb) / math.sqrt(n) if n > 1 else 0.0
    ci = (mean - 1.96 * se, mean + 1.96 * se)
    verdict = "win" if ci[0] > 0 else "loss" if ci[1] < 0 else "chop"
    return dict(bot=bot_name, opponent=opp_name, seeds=list(seeds), deals_per_seed=deals,
                n_deals=n, bb_deal=mean, ci_low=ci[0], ci_high=ci[1], verdict=verdict,
                errors=errors, elapsed=time.perf_counter() - t0)


def main():
    out_csv = "league/results.csv"
    pairs = list(itertools.combinations(SHORTLIST, 2))
    print(f"Running {len(pairs)} pairings x {len(SEEDS)} seeds x {DEALS} deals (official format, pooled)...",
          flush=True)
    rows = []
    exists = os.path.exists(out_csv) and os.path.getsize(out_csv) > 0
    f = open(out_csv, "a", newline="")
    w = csv.DictWriter(f, fieldnames=["bot", "opponent", "seed", "deals", "bb_deal", "ci_low", "ci_high",
                                       "verdict", "errors", "fallbacks", "think_s", "p50_ms", "p99_ms", "elapsed"],
                        extrasaction="ignore")
    if not exists:
        w.writeheader()
    for i, (a, b) in enumerate(pairs, 1):
        r = pooled_match(a, b)
        rows.append(r)
        row = dict(r)
        row["seed"] = "pooled:" + ",".join(str(s) for s in r["seeds"])
        row["deals"] = r["n_deals"]
        row["fallbacks"] = 0
        row["think_s"] = 0.0
        row["p50_ms"] = 0.0
        row["p99_ms"] = 0.0
        w.writerow(row)
        f.flush()
        print(f"[{i}/{len(pairs)}] {a} vs {b}: {r['verdict']} {r['bb_deal']:+.4f} bb/deal "
              f"CI[{r['ci_low']:+.4f},{r['ci_high']:+.4f}] n={r['n_deals']} errors={r['errors']} "
              f"elapsed={r['elapsed']:.1f}s", flush=True)
    f.close()

    points = {b: 0.0 for b in SHORTLIST}
    bb_sum = {b: 0.0 for b in SHORTLIST}
    bb_n = {b: 0 for b in SHORTLIST}
    record = {b: [0, 0, 0] for b in SHORTLIST}  # W L C
    h2h = {}
    for r in rows:
        a, b_, v, bb = r["bot"], r["opponent"], r["verdict"], r["bb_deal"]
        h2h[(a, b_)] = r
        h2h[(b_, a)] = dict(r, bot=b_, opponent=a, bb_deal=-bb, ci_low=-r["ci_high"], ci_high=-r["ci_low"],
                             verdict={"win": "loss", "loss": "win", "chop": "chop"}[v])
        if v == "win":
            points[a] += 1; record[a][0] += 1; record[b_][1] += 1
        elif v == "loss":
            points[b_] += 1; record[b_][0] += 1; record[a][1] += 1
        else:
            points[a] += 0.5; points[b_] += 0.5; record[a][2] += 1; record[b_][2] += 1
        bb_sum[a] += bb; bb_n[a] += 1
        bb_sum[b_] += -bb; bb_n[b_] += 1
    avg_bb = {b: (bb_sum[b] / bb_n[b] if bb_n[b] else 0.0) for b in SHORTLIST}
    standings = sorted(SHORTLIST, key=lambda b: (-points[b], -avg_bb[b]))
    top = standings[0]

    lines = []
    lines.append("# Round-robin leaderboard — official format (real results)\n\n")
    lines.append(f"Official-format round-robin: {len(SHORTLIST)} bots, {len(pairs)} pairings, "
                  f"seeds={list(SEEDS)} pooled ({len(SEEDS) * DEALS} deals/pairing), "
                  f"{DEALS} deals/seed x 2 halves/match — matches the competition's duplicate format "
                  f"(1000 deals x 2 halves per seed, pooled bb/deal, 95% CI verdict: win if CI entirely "
                  f">0, loss if entirely <0, chop otherwise). `harrier` (CFR-family research bot) is not "
                  f"yet merged to origin/main as of this run and is not included; add it and re-run once it "
                  f"lands.\n\n")
    lines.append("| Rank | Bot | Points | Record (W-L-C) | Avg bb/deal |\n")
    lines.append("| --- | --- | --- | --- | --- |\n")
    for rank, b in enumerate(standings, 1):
        w_, l_, c_ = record[b]
        lines.append(f"| {rank} | `{b}` | {points[b]:.1f} | {w_}-{l_}-{c_} | {avg_bb[b]:+.3f} |\n")

    lines.append("\n## Current default / what we would submit today\n\n")
    if top == "m5_challenger":
        r55 = record["m5_challenger"]
        lines.append(f"**`m5_challenger`** — tops this round-robin ({points['m5_challenger']:.1f} pts, "
                      f"{r55[0]}-{r55[1]}-{r55[2]}, avg {avg_bb['m5_challenger']:+.3f} bb/deal) and "
                      f"remains `bots/active.py`'s current `ACTIVE_BOT` default. This matches every prior "
                      f"validation this session: Kestrel, Osprey, both City-family bots, and (separately) "
                      f"Harrier have all failed to beat it with statistical significance in multi-seed "
                      f"pooled-CI testing. No change to `bots/active.py`.\n")
    else:
        h2h_row = h2h.get((top, "m5_challenger"))
        lines.append(f"**Standings leader is `{top}`, not `m5_challenger`.** Head-to-head vs "
                      f"`m5_challenger` in this run: {h2h_row['bb_deal']:+.4f} bb/deal, "
                      f"CI[{h2h_row['ci_low']:+.4f},{h2h_row['ci_high']:+.4f}], verdict={h2h_row['verdict']}, "
                      f"n={h2h_row['n_deals']} deals.\n\n")
        if h2h_row["verdict"] == "win":
            lines.append(f"This head-to-head CI is entirely positive for `{top}` — **recommended for "
                          f"promotion pending human review** (per standing policy, promotion needs a "
                          f"significant pooled-CI win across 8-10+ seeds x 1000 deals specifically vs "
                          f"`m5_challenger`; this run used {len(SEEDS)} seeds, so a deeper confirmation run "
                          f"is still warranted before flipping `bots/active.py`). `bots/active.py` was "
                          f"**not** modified by this run.\n")
        else:
            lines.append(f"Despite topping the round-robin standings overall, `{top}` does not beat "
                          f"`m5_challenger` head-to-head with a significant CI in this run, so "
                          f"`m5_challenger` remains the recommended default/submission. `bots/active.py` "
                          f"was **not** modified.\n")
            lines.append(f"\n**Current default / what we would submit today remains `m5_challenger`.**\n")

    lines.append("\n## Full pairwise results\n\n")
    lines.append("| Bot A | Bot B | bb/deal (A persp.) | CI | Verdict |\n")
    lines.append("| --- | --- | --- | --- | --- |\n")
    for r in rows:
        lines.append(f"| `{r['bot']}` | `{r['opponent']}` | {r['bb_deal']:+.4f} | "
                      f"[{r['ci_low']:+.4f},{r['ci_high']:+.4f}] | {r['verdict']} |\n")

    with open("league/leaderboard.md", "w") as f:
        f.writelines(lines)
    print("Wrote league/leaderboard.md", flush=True)


if __name__ == "__main__":
    main()
