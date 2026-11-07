"""Shared information-state abstraction for MCCFR+ training and runtime."""
import json
import math
from bots.common.cards import canonical_suits
from bots.common.equity import equity_vs_random
from game import Action, Street

_PREFLOP = None


def load_preflop():
    global _PREFLOP
    if _PREFLOP is None:
        try:
            from pathlib import Path
            _PREFLOP = json.loads((Path(__file__).resolve().parents[1] / "m1_equity" / "tables" / "preflop.json").read_text())
        except (OSError, ValueError):
            _PREFLOP = {}
    return _PREFLOP


def equity(obs):
    if obs.street == Street.PREFLOP:
        key = ";".join(f"{r}{s}" for r, s in canonical_suits(obs.hole_cards))
        value = load_preflop().get(key)
        if value is not None:
            return float(value)
    return equity_vs_random(tuple(obs.hole_cards), tuple(obs.board), 8)


def info_key(obs):
    ebin = min(9, int(equity(obs) * 10))
    pot_odds = obs.to_call / max(1, obs.pot + obs.to_call)
    obin = min(7, int(pot_odds * 8))
    spr = obs.my_stack / max(1, obs.pot)
    sprbin = min(7, int(spr * 2))
    # Imperfect-recall abstraction: compress each street to actor/action counts.
    # Pot odds, SPR, and the current legal mask retain the main size constraints.
    counts = {}
    for record in obs.action_history:
        if record.action in (Action.RAISE_HALF, Action.RAISE_POT):
            action_index = int(record.action) - int(Action.RAISE_HALF)
        else:
            action_index = 2  # folds terminate immediately; CHECK_CALL is grouped
        slot = (int(record.street), int(record.is_me), action_index)
        counts[slot] = min(3, counts.get(slot, 0) + 1)
    history = tuple(counts.get((street, is_me, action), 0)
                    for street in range(4) for is_me in range(2) for action in range(3))
    legal_mask = sum(1 << int(action) for action in obs.legal_actions)
    return json.dumps((obs.street.name, ebin, obin, sprbin, int(obs.is_button),
                       obs.raises_this_street, legal_mask, history), separators=(",", ":"))


def info_key_sequence(obs):
    """Use ordered public action history instead of merging sequences by counts."""
    ebin = min(9, int(equity(obs) * 10))
    pot_odds = obs.to_call / max(1, obs.pot + obs.to_call)
    obin = min(7, int(pot_odds * 8))
    spr = obs.my_stack / max(1, obs.pot)
    sprbin = min(7, int(spr * 2))
    legal_mask = sum(1 << int(action) for action in obs.legal_actions)
    history = tuple((int(record.street), int(record.is_me), int(record.action),
                     min(7, int(math.log2(max(1, record.street_total)))))
                    for record in obs.action_history)
    return json.dumps((obs.street.name, ebin, obin, sprbin, int(obs.is_button),
                       obs.raises_this_street, legal_mask, history), separators=(",", ":"))


def policy_from_regret(regrets, legal):
    weights = [max(0.0, regrets[a]) if Action(a) in legal else 0.0 for a in range(4)]
    total = sum(weights)
    if total <= 1e-12:
        n = len(legal)
        return [1.0 / n if Action(a) in legal else 0.0 for a in range(4)]
    return [x / total for x in weights]
