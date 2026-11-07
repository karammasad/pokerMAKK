"""Small-budget Monte Carlo equity strategy for Short Deck PLO5."""
import json
from pathlib import Path

from bots.common.equity import equity_vs_random
from bots.common.cards import canonical_suits
from game import Action, Street


_PREFLOP = None
_PARAMS = {"value_pot": 0.76, "value_half": 0.63, "margin": 0.04, "bluff_freq": 0.0}


def load():
    global _PREFLOP, _PARAMS
    root = Path(__file__).parent
    try:
        _PREFLOP = json.loads((root / "tables" / "preflop.json").read_text())
    except (OSError, ValueError):
        _PREFLOP = None
    try:
        _PARAMS.update(json.loads((root / "params.json").read_text()))
    except (OSError, ValueError):
        pass


def new_half(config, memory):
    memory["hands_played"] = 0


def estimate_equity(obs, budget_s=None, max_samples=32):
    return equity_vs_random(tuple(obs.hole_cards), tuple(obs.board), max_samples)


def choose_action(obs, memory):
    legal = obs.legal_actions
    if obs.street == Street.PREFLOP:
        equity = None
        if _PREFLOP:
            key = ";".join(f"{r}{s}" for r, s in canonical_suits(obs.hole_cards))
            equity = _PREFLOP.get(key)
        if equity is None:
            ranks = [c >> 2 for c in obs.hole_cards]
            suits = [c & 3 for c in obs.hole_cards]
            counts = [ranks.count(r) for r in set(ranks)]
            pairs = sum(n * (n - 1) // 2 for n in counts)
            gaps = sorted(set(ranks))
            connected = sum(1 for a, b in zip(gaps, gaps[1:]) if b - a <= 2)
            suit_pairs = sum(n * (n - 1) // 2 for n in [suits.count(s) for s in set(suits)])
            strength = 0.36 + 0.035 * pairs + 0.025 * connected + 0.018 * suit_pairs + 0.008 * sum(ranks)
            equity = min(0.74, max(0.24, strength))
    else:
        equity = estimate_equity(obs)
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    if obs.street == Street.RIVER and obs.to_call == 0 and Action.RAISE_HALF in legal:
        checked_to = any(not record.is_me and record.street == Street.RIVER and
                         record.action == Action.CHECK_CALL for record in obs.action_history)
        if checked_to and _PARAMS["bluff_freq"] > 0:
            draw = (obs.hand_index * 97 + sum(obs.hole_cards) * 31) % 10000 / 10000
            if draw < _PARAMS["bluff_freq"]:
                return Action.RAISE_HALF
    value_pot = _PARAMS["value_pot"] - (0.02 if obs.is_button else 0.0)
    value_half = _PARAMS["value_half"] - (0.02 if obs.is_button else 0.0)
    if Action.RAISE_POT in legal and equity >= value_pot:
        return Action.RAISE_POT
    if Action.RAISE_HALF in legal and equity >= value_half:
        return Action.RAISE_HALF
    if Action.CHECK_CALL in legal and (obs.to_call == 0 or equity >= odds + _PARAMS["margin"]):
        return Action.CHECK_CALL
    if Action.FOLD in legal:
        return Action.FOLD
    return Action.CHECK_CALL


def on_hand_end(result, memory):
    pass
