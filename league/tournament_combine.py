"""Combine the main 11-bot round-robin + messi's supplemental pairings
(both already appended to league/results.csv as seed="pooled:0,1,2" rows)
into one final 12-bot standings table and league/leaderboard.md.
"""
import csv
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SHORTLIST = [
    "m5_challenger", "m5_classic", "m5_counterplay", "kestrel", "osprey",
    "ederson", "mahrez", "telltide", "northstar", "m9_cfrplus", "aguero", "messi",
]
SEED_TAG = "pooled:0,1,2"


def main():
    rows = []
    with open("league/results.csv") as f:
        for r in csv.DictReader(f):
            if r.get("seed") == SEED_TAG and r["bot"] in SHORTLIST and r["opponent"] in SHORTLIST:
                rows.append(dict(bot=r["bot"], opponent=r["opponent"], bb_deal=float(r["bb_deal"]),
                                  ci_low=float(r["ci_low"]), ci_high=float(r["ci_high"]),
                                  verdict=r["verdict"], n_deals=int(r["deals"]), errors=int(r["errors"])))

    # keep only the latest row per unordered pair (in case of any re-run duplicates)
    by_pair = {}
    for r in rows:
        key = frozenset((r["bot"], r["opponent"]))
        by_pair[key] = r  # last one wins; file is append-only in run order so this is fine
    rows = list(by_pair.values())

    expected_pairs = set(frozenset(p) for p in itertools.combinations(SHORTLIST, 2))
    found_pairs = set(frozenset((r["bot"], r["opponent"])) for r in rows)
    missing = expected_pairs - found_pairs
    if missing:
        print(f"WARNING: missing {len(missing)} pairings: {missing}")

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
    lines.append(f"Official-format round-robin: {len(SHORTLIST)} bots, {len(rows)} pairings, "
                  f"3 seeds (0,1,2) pooled per pairing (3000 deals/pairing total), "
                  f"1000 deals/seed x 2 halves/match — matches the competition's duplicate format "
                  f"(1000 deals x 2 halves per seed, pooled bb/deal, 95% CI verdict: win if CI entirely "
                  f">0, loss if entirely <0, chop otherwise). `harrier` (CFR-family research bot) is not "
                  f"yet merged to origin/main as of this run and is not included; add it and re-run once it "
                  f"lands. `messi` was added mid-run (teammate push) and given the same treatment: full "
                  f"pooled pairings vs every other shortlist bot.\n\n")
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
                      f"remains `bots/active.py`'s current `ACTIVE_BOT` default. No change made.\n")
    else:
        h2h_row = h2h.get((top, "m5_challenger"))
        lines.append(f"**Standings leader is `{top}`, not `m5_challenger`.** Head-to-head vs "
                      f"`m5_challenger` in this run: {h2h_row['bb_deal']:+.4f} bb/deal, "
                      f"CI[{h2h_row['ci_low']:+.4f},{h2h_row['ci_high']:+.4f}], verdict={h2h_row['verdict']}, "
                      f"n={h2h_row['n_deals']} deals.\n\n")
        if h2h_row["verdict"] == "win":
            lines.append(f"This head-to-head CI is entirely positive for `{top}` over `m5_challenger` — "
                          f"**recommended for promotion pending human review** (standing policy requires a "
                          f"significant pooled-CI win across 8-10+ seeds x 1000 deals specifically vs "
                          f"`m5_challenger` before flipping `bots/active.py`; this run used 3 seeds, so a "
                          f"deeper confirmation run at 8-10 seeds is still warranted). `bots/active.py` was "
                          f"**not** modified by this run.\n")
        else:
            lines.append(f"Despite topping the round-robin standings overall, `{top}` does not beat "
                          f"`m5_challenger` head-to-head with a significant CI in this run "
                          f"(verdict={h2h_row['verdict']}), so promotion is not indicated on this evidence "
                          f"alone. `bots/active.py` was **not** modified.\n")
        # Also surface any OTHER bot that beats m5_challenger head-to-head significantly, even if not top
        beats_m5 = [b for b in SHORTLIST if b != "m5_challenger" and h2h.get((b, "m5_challenger"), {}).get("verdict") == "win"]
        if beats_m5:
            lines.append(f"\n**Bots that beat `m5_challenger` head-to-head with a significant CI in this "
                          f"run:** {', '.join('`%s` (%+.4f bb/deal)' % (b, h2h[(b,'m5_challenger')]['bb_deal']) for b in beats_m5)}. "
                          f"All flagged for deeper confirmation (8-10+ seeds) before any promotion decision.\n")

    lines.append("\n## Full pairwise results\n\n")
    lines.append("| Bot A | Bot B | bb/deal (A persp.) | CI | Verdict |\n")
    lines.append("| --- | --- | --- | --- | --- |\n")
    for a, b_ in itertools.combinations(SHORTLIST, 2):
        r = h2h.get((a, b_))
        if r:
            lines.append(f"| `{a}` | `{b_}` | {r['bb_deal']:+.4f} | "
                          f"[{r['ci_low']:+.4f},{r['ci_high']:+.4f}] | {r['verdict']} |\n")

    with open("league/leaderboard.md", "w") as f:
        f.writelines(lines)
    print(f"Wrote league/leaderboard.md with {len(rows)} pairings, standings top: {top}")
    print("Standings:")
    for rank, b in enumerate(standings, 1):
        w_, l_, c_ = record[b]
        print(f"  {rank}. {b}: {points[b]:.1f} pts {w_}-{l_}-{c_} avg {avg_bb[b]:+.3f} bb/deal")


if __name__ == "__main__":
    main()
