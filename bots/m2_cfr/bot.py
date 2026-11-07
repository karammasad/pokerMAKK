"""Regret-matching strategy over coarse equity and pot-odds abstractions."""
import json
from pathlib import Path
from bots.m1_equity import bot as base
from game import Action

TABLE = Path(__file__).parent / "tables" / "strategy.json"
_POLICY = None


def load():
    global _POLICY
    try:
        _POLICY = json.loads(TABLE.read_text())
    except (OSError, ValueError):
        _POLICY = None


def new_half(config, memory):
    base.new_half(config, memory)


def choose_action(obs, memory):
    fallback = base.choose_action(obs, memory)
    if not _POLICY or obs.street.name == "PREFLOP":
        return fallback
    equity = base.estimate_equity(obs)
    bucket = min(9, int(equity * 10))
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    ob = min(4, int(odds * 5))
    strategy = _POLICY.get(f"{obs.street.name}:{bucket}:{ob}")
    if not strategy:
        return fallback
    actions = [Action.FOLD, Action.CHECK_CALL, Action.RAISE_HALF, Action.RAISE_POT]
    weights = [max(0.0, float(strategy[i])) for i in range(4)]
    total = sum(weights)
    if not total:
        return fallback
    # Deterministic mixed-strategy sampling per state avoids global RNG state.
    x = ((sum(obs.hole_cards) * 131 + sum(obs.board) * 17 + obs.hand_index * 29) % 10000) / 10000 * total
    for action, weight in zip(actions, weights):
        x -= weight
        if x <= 0 and action in obs.legal_actions:
            return action
    return fallback


def on_hand_end(result, memory):
    pass
