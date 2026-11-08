"""Atlas private City-engine snapshot from 7d004f6; shared opponents stay frozen."""
"""Shared engine for the Man City bot family.

Every City bot is this engine plus a PROFILE (dict of thresholds). The engine
fuses the strongest measured pieces in the repo:

* m5_counterplay preflop table and postflop fold/value thresholds (the best
  head-to-head base),
* m7_precision near-threshold equity refinement (with a think-time pace guard),
* m5_challenger switch against sustained aggression (it crushes spew bots),
* per-half opponent model (raise rate, fold-to-pressure rate) that scales bluff
  frequency, plus optional traps/slowplays, floats, bluff-raises and a
  stop-loss that drops "ballsy" play back to a safe profile when losing.

All per-half state lives in `memory`. No module globals except constants.
"""
import json
from pathlib import Path

import game
from bots.common.cards import canonical_suits
from bots.atlas.equity import estimate as atlas_equity
from bots.m1_equity import bot as base
from bots.m5_classic import bot as m5
from bots.m5_counterplay import bot as core
from game import Action, Street

DEFAULTS = {
    # postflop thresholds (equity vs a random hand)
    "pot_cut": 0.76, "half_cut": 0.375, "reraise_cut": 0.90, "call_margin": 0.30,
    # preflop thresholds (table equity)
    "pre_pot": 0.76, "pre_open": 0.56, "pre_raise": 0.63, "pre_slack": 0.04,
    "pre_light": 0.0, "pre_light_floor": 0.50,
    # sampling
    "base_samples": 32, "refine_samples": 64, "band": 0.04,
    "no_refine_s": 1.0, "panic_s": 1.7, "panic_samples": 8,
    # opponent handling
    "aggro_mode": "m5", "aggro_rate": 0.45, "min_actions": 40,
    # deception
    "bluff": 0.0, "bluff_eq_max": 0.25, "bluff_adapt": True, "bluff_pot": False,
    "bluff_any_street": False, "bluff_raise": 0.0, "bluff_raise_band": (0.15, 0.45),
    "slowplay": 0.0, "float": 0.0,
    # teammate-proven counterplay attacks (gated by measured fold response)
    "tb_turn": False, "tb_river": False, "tb_flop_mix": False, "tb_gate": True,
    "open_mix": False, "river_call_margin": None, "station_thin": False,
    "catch_rate": None, "rr_cut": None, "cb_exploit": False, "cb_margin": 0.08, "cb_reraise": 0.78,
    # stop-loss (in big blinds, 0 disables) -> switch to SAFE override
    "stop_loss_bb": 0,
}
SAFE = {"tb_river": False, "tb_flop_mix": False, "open_mix": False, "bluff": 0.0, "bluff_raise": 0.0, "float": 0.0, "slowplay": 0.0, "pre_light": 0.0,
        "half_cut": 0.42, "pot_cut": 0.80, "call_margin": 0.32}


def load():
    core.load()
    m5.load()


def new_half(config, memory):
    core.new_half(config, memory)
    m5.new_half(config, memory)
    memory["_city"] = {"hand": -1, "seen": 0, "acts": 0, "raises": 0,
                       "made": 0, "folded": 0, "pending": False, "net": 0,
                       "tb_trials": 0, "tb_folds": 0, "tb_pending": None,
                       "cb_opps": 0, "cb_bets": 0, "chk": None}


def _draw(obs, salt):
    return (obs.hand_index * 97 + sum(obs.hole_cards) * 31 + salt * 7919) % 10000 / 10000


def _observe(obs, st):
    if st["hand"] != obs.hand_index:
        st["hand"], st["seen"] = obs.hand_index, 0
    hist = obs.action_history
    for idx in range(st["seen"], len(hist)):
        rec = hist[idx]
        first = idx == 0 or hist[idx - 1].street != rec.street
        if rec.street != Street.PREFLOP:
            if rec.is_me and first and rec.action == Action.CHECK_CALL:
                st["chk"] = rec.street
            elif not rec.is_me and st["chk"] == rec.street:
                st["cb_opps"] += 1
                if rec.action in (Action.RAISE_HALF, Action.RAISE_POT):
                    st["cb_bets"] += 1
                st["chk"] = None
        if not rec.is_me:
            st["acts"] += 1
            if rec.action in (Action.RAISE_HALF, Action.RAISE_POT):
                st["raises"] += 1
    st["seen"] = len(obs.action_history)


def _params(profile, st):
    p = dict(DEFAULTS)
    p.update(profile)
    loss = p["stop_loss_bb"]
    if loss and st["net"] < -loss * game.BIG_BLIND:
        p.update(SAFE)
    return p


def _always_bets(st):
    """Opponent bets (almost) every time we check to them: their bet is uninformative."""
    return st["cb_opps"] >= 20 and (st["cb_bets"] + 1.0) / (st["cb_opps"] + 2.0) >= 0.75


def _facing_bet_after_check(obs):
    recs = [r for r in obs.action_history if r.street == obs.street]
    return (len(recs) == 2 and recs[0].is_me and recs[0].action == Action.CHECK_CALL
            and recs[1].action in (Action.RAISE_HALF, Action.RAISE_POT))


def _facing_reraise(obs):
    """The opponent raised a bet/raise of ours on this street: their range is very strong."""
    recs = [r for r in obs.action_history if r.street == obs.street]
    return (len(recs) >= 2 and recs[-1].action in (Action.RAISE_HALF, Action.RAISE_POT)
            and any(r.is_me and r.action in (Action.RAISE_HALF, Action.RAISE_POT) for r in recs[:-1]))


def _raise_rate(st):
    return (st["raises"] + 2.0) / (st["acts"] + 10.0)


def _fold_rate(st):
    return (st["folded"] + 2.0) / (st["made"] + 6.0)


def _mix(obs):
    return (obs.hand_index * 31 + sum(card >> 2 for card in obs.hole_cards)) % 4 == 0


def _tb_ok(p, st):
    if not p["tb_gate"]:
        return True
    t, f = st["tb_trials"], st["tb_folds"]
    return t < 12 or (f + 2) / (t + 4) >= 1 / 3


def _pick(legal, *prefs):
    for a in prefs:
        if a in legal:
            return a
    return Action.CHECK_CALL if Action.CHECK_CALL in legal else legal[0]


def _preflop(p, obs, memory, st):
    legal = obs.legal_actions
    table = core._PREFLOP
    key = ";".join(f"{r}{s}" for r, s in canonical_suits(obs.hole_cards))
    eq = table.get(key) if table else None
    if eq is None:
        return core.choose_action(obs, memory)
    off = 0.02 if obs.is_button else 0.0
    if eq >= p["pre_pot"] - off and Action.RAISE_POT in legal:
        return Action.RAISE_POT
    opening = obs.is_button and obs.raises_this_street == 0
    if eq >= (p["pre_open"] if opening else p["pre_raise"] - off) and Action.RAISE_HALF in legal:
        return Action.RAISE_HALF
    if (p["pre_light"] and eq >= p["pre_light_floor"] and Action.RAISE_HALF in legal
            and _draw(obs, 1) < p["pre_light"]):
        return Action.RAISE_HALF
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    if obs.to_call and eq < odds + p["pre_slack"] and Action.FOLD in legal:
        return Action.FOLD
    if (p["open_mix"] and opening and eq >= 0.50 and Action.RAISE_HALF in legal and _mix(obs)):
        return Action.RAISE_HALF
    return Action.CHECK_CALL


def _equity(p, obs, memory, thresholds):
    hole, board = tuple(obs.hole_cards), tuple(obs.board)
    spent = memory.get("_think_s", 0.0)
    if spent >= 2.7:
        return atlas_equity(obs, memory, 4)
    if spent > p["panic_s"]:
        return atlas_equity(obs, memory, p["panic_samples"])
    est = atlas_equity(obs, memory, p["base_samples"])
    if spent > p["no_refine_s"]:
        return est
    if min(abs(est - t) for t in thresholds) <= p["band"]:
        est = atlas_equity(obs, memory, p["refine_samples"])
    return est


def choose_action(profile, obs, memory):
    st = memory["_city"]
    _observe(obs, st)
    if st["tb_pending"] == obs.hand_index:
        st["tb_trials"] += 1  # opponent did not fold: we are deciding again
        st["tb_pending"] = None
    p = _params(profile, st)
    legal = obs.legal_actions
    if obs.street == Street.PREFLOP:
        action = _preflop(p, obs, memory, st)
        memory_raise = action in (Action.RAISE_HALF, Action.RAISE_POT)
        st["pending"] = st["pending"] or memory_raise
        return action

    rate = _raise_rate(st)
    aggressive = st["acts"] >= p["min_actions"] and rate >= p["aggro_rate"]
    if aggressive and (p["aggro_mode"] == "m5" or (p["aggro_mode"] == "hybrid" and rate >= 0.90)):
        return _aggressor(obs, memory)

    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    margin = p["call_margin"] - (0.08 if aggressive and p["aggro_mode"] in ("calldown", "hybrid") else 0.0)
    if (p["catch_rate"] is not None and not aggressive and st["acts"] >= p["min_actions"]
            and rate >= p["catch_rate"]):
        margin -= 0.07  # bluff-catcher: opponent raises often but not like a maniac
    exploit = (p["cb_exploit"] and obs.to_call and _always_bets(st) and _facing_bet_after_check(obs))
    if exploit:
        margin = min(margin, p["cb_margin"])
    if p["river_call_margin"] is not None and obs.street == Street.RIVER and not exploit:
        margin = min(margin, p["river_call_margin"])
    thin = p["station_thin"] and st["made"] >= 40 and _fold_rate(st) < 0.20
    if thin:
        p["half_cut"] -= 0.04
        p["pot_cut"] -= 0.03
    if obs.to_call:
        thresholds = (p["reraise_cut"] if not exploit else p["cb_reraise"], odds + margin)
    else:
        thresholds = (p["pot_cut"], p["half_cut"])
    eq = _equity(p, obs, memory, thresholds)

    scale = max(0.3, min(2.0, _fold_rate(st) / 0.33)) if p["bluff_adapt"] else 1.0
    big = Action.RAISE_POT if p["bluff_pot"] else Action.RAISE_HALF

    def aggress(action):
        st["pending"] = True
        return action

    if obs.to_call:
        if (p["rr_cut"] is not None and obs.to_call > 2 and Action.FOLD in legal
                and eq < p["rr_cut"] and _facing_reraise(obs)):
            return Action.FOLD
        if eq >= (p["cb_reraise"] if exploit else p["reraise_cut"]):
            return aggress(_pick(legal, Action.RAISE_POT, Action.RAISE_HALF))
        if (p["bluff_raise"] and p["bluff_raise_band"][0] <= eq <= p["bluff_raise_band"][1]
                and obs.raises_this_street == 0 and _draw(obs, 3) < p["bluff_raise"] * scale
                and big in legal):
            return aggress(big)
        if obs.to_call > 2 and eq < odds + margin and Action.FOLD in legal:
            if (p["float"] and obs.street == Street.FLOP and eq >= odds + 0.08
                    and _draw(obs, 4) < p["float"]):
                return Action.CHECK_CALL
            return Action.FOLD
        return Action.CHECK_CALL

    if eq >= p["pot_cut"] and Action.RAISE_POT in legal:
        if (p["slowplay"] and obs.street in (Street.FLOP, Street.TURN) and eq >= 0.92
                and _draw(obs, 5) < p["slowplay"]):
            return Action.CHECK_CALL
        return aggress(Action.RAISE_POT)
    if eq >= p["half_cut"] and Action.RAISE_HALF in legal:
        return aggress(Action.RAISE_HALF)
    if Action.RAISE_HALF in legal and eq < 0.375 and not thin:
        eligible = ((obs.street == Street.TURN and p["tb_turn"])
                    or (obs.street == Street.RIVER and p["tb_river"])
                    or (obs.street == Street.FLOP and p["tb_flop_mix"] and _mix(obs)))
        if eligible and _tb_ok(p, st):
            st["tb_pending"] = obs.hand_index
            return aggress(Action.RAISE_HALF)
    if p["bluff"] and eq <= p["bluff_eq_max"] and big in legal and not thin:
        checked_to = any(not r.is_me and r.street == Street.RIVER and r.action == Action.CHECK_CALL
                         for r in obs.action_history)
        spot = (obs.street == Street.RIVER and checked_to) or (
            p["bluff_any_street"] and obs.street != Street.RIVER)
        if spot and _draw(obs, 2) < min(0.6, p["bluff"] * scale):
            return aggress(big)
    return Action.CHECK_CALL


def on_hand_end(profile, result, memory):
    st = memory.get("_city")
    if st is not None:
        if st["tb_pending"] == result.hand_index:
            st["tb_trials"] += 1
            if not result.went_to_showdown and result.winner == "me":
                st["tb_folds"] += 1
            st["tb_pending"] = None
        st["net"] += result.my_net
        if st["pending"]:
            st["made"] += 1
            if result.winner == "me" and not result.went_to_showdown:
                st["folded"] += 1
            st["pending"] = False
    core.on_hand_end(result, memory)


def _aggressor(obs, memory):
    """Classic value/call policy with reusable samples and a late-half guard."""
    legal = obs.legal_actions
    spent = memory.get('_think_s', 0.0)
    samples = 4 if spent >= 2.7 else 8 if spent >= 1.6 else 32
    eq = atlas_equity(obs, memory, samples)
    offset = 0.02 if obs.is_button else 0.0
    if eq >= 0.76 - offset and Action.RAISE_POT in legal:
        return Action.RAISE_POT
    if eq >= 0.63 - offset and Action.RAISE_HALF in legal:
        return Action.RAISE_HALF
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    margin = 0.20 if obs.to_call > 2 else 0.04
    if obs.to_call and eq < odds + margin and Action.FOLD in legal:
        return Action.FOLD
    if (obs.street == Street.RIVER and not obs.to_call and eq <= 0.25
            and Action.RAISE_HALF in legal
            and any(not r.is_me and r.street == Street.RIVER and r.action == Action.CHECK_CALL
                    for r in obs.action_history)):
        return Action.RAISE_HALF
    return _pick(legal, Action.CHECK_CALL)
