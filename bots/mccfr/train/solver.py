"""Train an abstracted external-sampling MCCFR+ policy on the official game.

The tree transitions and terminal utilities are exact. Chance is sampled by
deal; opponent actions are sampled from the current regret-matching policy;
the traverser's actions are enumerated. The information-state abstraction
groups cards by equity/pot-odds/SRP buckets and can either compress public
history to action counts or preserve the ordered action sequence. Card
abstraction remains imperfect recall in both modes, so this is a research
prototype, not an equilibrium guarantee for the unabstracted tournament game.
"""
import argparse
from copy import deepcopy
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import game
from game import Action
from bots.mccfr.core import info_key, info_key_sequence, policy_from_regret
from evaluator import warmup


class Solver:
    def __init__(self, seed, node_limit, info_key_fn=info_key):
        self.rng = random.Random(seed)
        self.info_key_fn = info_key_fn
        self.nodes = {}
        self.node_limit = node_limit
        self.visited = 0
        self.total_visited = 0

    def _entry(self, key):
        return self.nodes.setdefault(key, {"regrets": [0.0] * 4,
                                           "strategy_sum": [0.0] * 4,
                                           "visits": 0})

    def _sample(self, policy, legal):
        draw = self.rng.random()
        running = 0.0
        last = legal[-1]
        for action in legal:
            running += policy[int(action)]
            if draw <= running:
                return action
        return last

    def _rollout(self, state, traverser):
        """Finish rare depth-capped branches with a legal equity baseline."""
        from bots.m1_equity import bot as base
        if not getattr(base, "_PREFLOP", None):
            base.load()
        memory = {}
        while not state.is_terminal:
            seat = state.to_act
            obs = state.observation(seat)
            action = base.choose_action(obs, memory)
            if action not in obs.legal_actions:
                action = game.default_action(obs.to_call)
            state.apply(action)
        return state.result().nets[traverser] / game.BIG_BLIND

    def traverse(self, state, traverser, own_reach, iteration, depth=0):
        if state.is_terminal:
            return state.result().nets[traverser] / game.BIG_BLIND
        if depth >= 48 or self.visited >= self.node_limit:
            return self._rollout(state, traverser)
        self.visited += 1
        player = state.to_act
        obs = state.observation(player)
        legal = obs.legal_actions
        key = self.info_key_fn(obs)
        entry = self._entry(key)
        strategy = policy_from_regret(entry["regrets"], legal)
        if player != traverser:
            action = self._sample(strategy, legal)
            child = deepcopy(state)
            child.apply(action)
            return self.traverse(child, traverser, own_reach, iteration, depth + 1)

        action_values = [0.0] * 4
        node_value = 0.0
        for action in legal:
            child = deepcopy(state)
            child.apply(action)
            value = self.traverse(child, traverser,
                                  own_reach * strategy[int(action)], iteration, depth + 1)
            action_values[int(action)] = value
            node_value += strategy[int(action)] * value
        for action in legal:
            a = int(action)
            # CFR+: truncate cumulative counterfactual regrets at zero.
            entry["regrets"][a] = max(0.0, entry["regrets"][a] + action_values[a] - node_value)
            entry["strategy_sum"][a] += (iteration + 1) * own_reach * strategy[a]
        entry["visits"] += 1
        return node_value

    def iteration(self, iteration, seed):
        hand = game.Game(game.make_deal(seed, iteration), game.button_for_deal(iteration), iteration)
        self.visited = 0
        self.traverse(hand, 0, 1.0, iteration)
        self.total_visited += self.visited
        hand = game.Game(game.make_deal(seed, iteration), game.button_for_deal(iteration), iteration)
        self.visited = 0
        self.traverse(hand, 1, 1.0, iteration)
        self.total_visited += self.visited


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=20000)
    parser.add_argument("--seed", default="mccfrplus-v1")
    parser.add_argument("--node-limit", type=int, default=30000,
                        help="maximum traversed decision nodes per player walk")
    parser.add_argument("--history-abstraction", choices=("compact", "sequence"), default="compact",
                        help="merge histories by action counts, or preserve the ordered public action sequence")
    parser.add_argument("--out", default=str(Path(__file__).parents[1] / "tables" / "strategy.json"))
    args = parser.parse_args()
    if args.iterations < 1 or args.node_limit < 1:
        parser.error("--iterations and --node-limit must be positive")
    warmup()
    key_fn = info_key if args.history_abstraction == "compact" else info_key_sequence
    solver = Solver(args.seed, args.node_limit, key_fn)
    started = time.perf_counter()
    for i in range(args.iterations):
        solver.iteration(i, args.seed)
        if (i + 1) % max(1, args.iterations // 20) == 0:
            print(f"iteration={i+1}/{args.iterations} infosets={len(solver.nodes)} "
                  f"decision_nodes={solver.total_visited} elapsed={time.perf_counter()-started:.1f}s", flush=True)
    policy = {}
    for key, entry in solver.nodes.items():
        avg = entry["strategy_sum"]
        total = sum(avg)
        if total > 1e-12:
            probs = [x / total for x in avg]
        else:
            probs = [0.0, 1.0, 0.0, 0.0]
        policy[key] = {"p": [round(x, 7) for x in probs], "visits": entry["visits"]}
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"metadata": {
        "algorithm": "external-sampling MCCFR+", "iterations": args.iterations,
        "seed": str(args.seed), "node_limit_per_walk": args.node_limit,
        "abstraction": f"equity/pot-odds/SRP buckets with {args.history_abstraction} public action history (imperfect card recall)",
        "training_seconds": round(time.perf_counter() - started, 3),
    }, "infosets": policy}, separators=(",", ":")))
    print(f"saved {len(policy)} infosets to {output}; elapsed={time.perf_counter()-started:.1f}s")


if __name__ == "__main__":
    main()
