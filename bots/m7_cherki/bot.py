"""M7 Cherki - combined policy: M5 counterplay core + M7 precision sampling + bounded adaptation.

* Preflop: the refined counterplay table and its open/raise/fold rules.
* Postflop: counterplay thresholds, with equity re-estimated at a higher sample
  count only when the first estimate lands near an action threshold (M7 idea).
* Adaptation: if the opponent's shrunk raise frequency stays high, postflop play
  switches to M5 challenger (better against aggressive spew); else counterplay.
"""
from bots.m5_counterplay import bot as core
from bots.m5_challenger import bot as m5
from bots.m1_equity import bot as base
from bots.common.equity import equity_vs_random
from game import Action, Street

CONFIG = {"base_samples": 32, "refine_samples": 64, "band": 0.04, "adapt": True,
          "aggro_rate": 0.45, "min_actions": 40,
          "no_refine_s": 1.8, "panic_s": 3.0, "panic_samples": 12}


def load():
    core.load()
    m5.load()


def new_half(config, memory):
    core.new_half(config, memory)
    m5.new_half(config, memory)
    memory["_cherki_hand"] = -1
    memory["_cherki_seen"] = 0
    memory["_cherki_opp_actions"] = 0
    memory["_cherki_opp_raises"] = 0
    memory["_cherki_opp_folds"] = 0


def _observe(obs, memory):
    if memory.get("_cherki_hand") != obs.hand_index:
        memory["_cherki_hand"] = obs.hand_index
        memory["_cherki_seen"] = 0
    history = obs.action_history
    for record in history[memory.get("_cherki_seen", 0):]:
        if record.is_me:
            continue
        memory["_cherki_opp_actions"] += 1
        if record.action in (Action.RAISE_HALF, Action.RAISE_POT):
            memory["_cherki_opp_raises"] += 1
        elif record.action == Action.FOLD:
            memory["_cherki_opp_folds"] += 1
    memory["_cherki_seen"] = len(history)


def _aggressive(memory):
    """True once the opponent has shown a sustained high raise frequency."""
    n = memory["_cherki_opp_actions"]
    if not CONFIG["adapt"] or n < CONFIG["min_actions"]:
        return False
    rate = (memory["_cherki_opp_raises"] + 2.0) / (n + 10.0)
    return rate >= CONFIG["aggro_rate"]


def _thresholds(obs, fold_margin, half_cut):
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    if obs.to_call:
        return (0.90, odds + fold_margin)
    return (0.76, half_cut)


def _equity(obs, memory, fold_margin, half_cut):
    hole, board = tuple(obs.hole_cards), tuple(obs.board)
    spent = memory.get("_think_s", 0.0)
    # Pace guard: stay under the ~4 s per-half target on showdown-heavy matchups.
    if spent > CONFIG["panic_s"]:
        return equity_vs_random(hole, board, CONFIG["panic_samples"])
    estimate = equity_vs_random(hole, board, CONFIG["base_samples"])
    if spent > CONFIG["no_refine_s"]:
        return estimate
    near = min(abs(estimate - t) for t in _thresholds(obs, fold_margin, half_cut))
    if near <= CONFIG["band"]:
        estimate = equity_vs_random(hole, board, CONFIG["refine_samples"])
    return estimate


def choose_action(obs, memory):
    _observe(obs, memory)
    if obs.street == Street.PREFLOP:
        return core.choose_action(obs, memory)
    legal = obs.legal_actions
    if _aggressive(memory):
        # Spewy opponents: M5's wider calls and value raises earn far more.
        return m5.choose_action(obs, memory)
    fold_margin = 0.30
    half_cut = 0.375
    equity = _equity(obs, memory, fold_margin, half_cut)
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    if obs.to_call:
        if equity >= 0.90 and Action.RAISE_POT in legal:
            return Action.RAISE_POT
        if equity >= 0.90 and Action.RAISE_HALF in legal:
            return Action.RAISE_HALF
        if obs.to_call > 2 and equity < odds + fold_margin and Action.FOLD in legal:
            return Action.FOLD
        return Action.CHECK_CALL
    if equity >= 0.76 and Action.RAISE_POT in legal:
        return Action.RAISE_POT
    if equity >= half_cut and Action.RAISE_HALF in legal:
        return Action.RAISE_HALF
    return Action.CHECK_CALL


def on_hand_end(result, memory):
    core.on_hand_end(result, memory)
