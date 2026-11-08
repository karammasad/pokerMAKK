"""In-process duplicate-deal league for strategies implementing the bot API."""
import argparse
import csv
import importlib
import math
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import game
from game import Action, AgentConfig
from bots.common.safe import wrap
from league.zoo.simple import factory
from bots.portfolio import factory as portfolio_factory, names as portfolio_names

ZOO = ["random", "calling_station", "always_half", "always_pot", "nit", "loose_passive", "maniac", "shover", "fold_to_raise"]
PORTFOLIO = list(portfolio_names())
RESEARCH_CANDIDATES = PORTFOLIO + [
    "m1_equity", "m2_cfr", "m3_exploit", "m4_learned", "m5_challenger",
    "m5_counterplay", "m7_cherki", "m6_safeadapt", "m7_precision", "m8_bayes_types", "m9_cfrplus", "m10_seq_cfr", "m11_chosen", "haaland", "de_bruyne", "rodri", "foden", "bernardo", "grealish", "mccfr",
]


def load_bot(name):
    if name in ZOO:
        return factory(name)
    if name in PORTFOLIO:
        return portfolio_factory(name)
    mod = importlib.import_module(f"bots.{name}.bot")
    hook = getattr(mod, "load", None)
    if hook:
        hook()
    return mod


def play_half(bot_a, bot_b, seed, half, deals):
    a_seat = 0 if half == 1 else 1
    bots = (bot_a, bot_b) if a_seat == 0 else (bot_b, bot_a)
    memories = [{}, {}]
    cfg = AgentConfig(num_hands=deals)
    for b, m in zip(bots, memories):
        b.new_half(cfg, m)
    nets = []
    errors = 0
    for i in range(deals):
        g = game.Game(game.make_deal(str(seed), i), game.button_for_deal(i), i)
        while not g.is_terminal:
            seat = g.to_act
            obs = g.observation(seat)
            try:
                action = bots[seat].choose_action(obs, memories[seat])
                if action not in obs.legal_actions:
                    errors += 1
                    action = game.default_action(obs.to_call)
            except Exception:
                errors += 1
                action = game.default_action(obs.to_call)
            g.apply(action)
        r = g.result()
        nets.append(r.nets[a_seat])
        for seat in (0, 1):
            try:
                bots[seat].on_hand_end(g.hand_result(seat), memories[seat])
            except Exception:
                errors += 1
    return nets, errors, memories


def match(bot_name, opp_name, seed, deals):
    raw = load_bot(bot_name)
    wrapped = wrap(raw)
    opp = wrap(load_bot(opp_name))
    halves = []
    errors = 0
    fallbacks = 0
    think = []
    decision_ms = []
    t0 = time.perf_counter()
    for h in (1, 2):
        n, err, memories = play_half(wrapped, opp, seed, h, deals)
        halves.append(n)
        errors += err
        ourmem = memories[0 if h == 1 else 1]
        fallbacks += ourmem.get("_fallbacks", 0)
        think.append(ourmem.get("_think_s", 0.0))
        decision_ms.extend(ourmem.get("_decision_ms", []))
    paired_bb = [(halves[0][i] + halves[1][i]) / game.BIG_BLIND for i in range(deals)]
    mean = statistics.mean(paired_bb) if paired_bb else 0.0
    se = statistics.stdev(paired_bb) / math.sqrt(deals) if deals > 1 else 0.0
    ci = (mean - 1.96 * se, mean + 1.96 * se)
    verdict = "win" if ci[0] > 0 else "loss" if ci[1] < 0 else "chop"
    ordered = sorted(decision_ms)
    p50 = statistics.median(ordered) if ordered else 0.0
    p99 = ordered[max(0, math.ceil(0.99 * len(ordered)) - 1)] if ordered else 0.0
    return dict(bot=bot_name, opponent=opp_name, seed=seed, deals=deals, bb_deal=mean,
                ci_low=ci[0], ci_high=ci[1], verdict=verdict, errors=errors,
                fallbacks=fallbacks, think_s=max(think, default=0.0),
                think_h1_s=think[0] if think else 0.0, think_h2_s=think[1] if len(think) > 1 else 0.0,
                p50_ms=p50, p99_ms=p99, elapsed=time.perf_counter()-t0)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--bot", default="m1_equity", help="strategy module or portfolio candidate")
    p.add_argument("--opp", default="all", help="comma-separated opponents, or all (zoo + portfolio)")
    p.add_argument("--zoo", choices=["all"], help="alias for --opp all")
    p.add_argument("--deals", type=int, default=1000)
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--seed-start", type=int, default=0, help="first seed in the consecutive range")
    p.add_argument("--timing", action="store_true")
    p.add_argument("--out", default="league/results.csv")
    args = p.parse_args()
    opponents = ZOO + RESEARCH_CANDIDATES if args.zoo or args.opp == "all" else [x.strip() for x in args.opp.split(",")]
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    exists = os.path.exists(args.out)
    with open(args.out, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["bot", "opponent", "seed", "deals", "bb_deal", "ci_low", "ci_high", "verdict", "errors", "fallbacks", "think_s", "p50_ms", "p99_ms", "elapsed"], extrasaction="ignore")
        if not exists or os.path.getsize(args.out) == 0:
            w.writeheader()
        for opponent in opponents:
            for seed in range(args.seed_start, args.seed_start + args.seeds):
                row = match(args.bot, opponent, seed, args.deals)
                w.writerow(row)
                f.flush()
                print(f"{row['bot']} vs {opponent} seed={seed}: {row['verdict']} {row['bb_deal']:+.3f} bb/deal CI[{row['ci_low']:+.3f},{row['ci_high']:+.3f}] errors={row['errors']} fallbacks={row['fallbacks']} think h1/h2={row['think_h1_s']:.3f}/{row['think_h2_s']:.3f}s p50/p99={row['p50_ms']:.3f}/{row['p99_ms']:.3f}ms")

if __name__ == "__main__":
    main()
