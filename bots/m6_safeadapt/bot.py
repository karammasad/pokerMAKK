"""M5-anchored adaptation with a Bayesian gate on weak river bluffs.

This is a small research prototype inspired by safe opponent adaptation. It
keeps M5 as the anchor, uses only public action responses, and caps river-bluff
suppression changes per half. It is not a reproduction of SafeAdapt-Poker.
"""
from bots.m5_challenger import bot as anchor
from game import Action, Street


def load():
    anchor.load()


def new_half(config, memory):
    anchor.new_half(config, memory)
    memory["_m6_hand"] = -1
    memory["_m6_seen"] = 0
    memory["_m6_pending_bluff"] = False
    memory["_m6_river_half_response"] = [0, 0]  # folds, continues
    memory["_m6_raises"] = 0
    memory["_m6_opp_actions"] = 0
    memory["_m6_changes"] = 0
    memory["_m6_change_budget"] = max(1, int(getattr(config, "num_hands", 1000)) // 20)


def _record_pending(memory, folded):
    if memory.get("_m6_pending_bluff"):
        memory["_m6_river_half_response"][0 if folded else 1] += 1
        memory["_m6_pending_bluff"] = False


def _observe(obs, memory):
    if memory.get("_m6_hand") != obs.hand_index:
        memory["_m6_hand"] = obs.hand_index
        memory["_m6_seen"] = 0
    history = obs.action_history
    for record in history[memory.get("_m6_seen", 0):]:
        if record.is_me:
            if record.street == Street.RIVER and record.action == Action.RAISE_HALF:
                # The current public river board lets us distinguish M5's weak
                # bluff from its ordinary value bet without revealing anything.
                memory["_m6_pending_bluff"] = anchor.base.estimate_equity(obs) <= 0.25
        else:
            memory["_m6_opp_actions"] += 1
            if record.action in (Action.RAISE_HALF, Action.RAISE_POT):
                memory["_m6_raises"] += 1
            if memory.get("_m6_pending_bluff"):
                _record_pending(memory, record.action == Action.FOLD)
    memory["_m6_seen"] = len(history)


def _wilson_lower(successes, failures, z=1.645):
    """One-sided 90% Wilson lower bound with a Beta(2, 5) prior."""
    alpha = successes + 2.0
    beta = failures + 5.0
    n = alpha + beta
    p = alpha / n
    z2 = z * z
    return max(0.0, (p + z2 / (2 * n) - z * ((p * (1 - p) / n + z2 / (4 * n * n)) ** 0.5)) / (1 + z2 / n))


def _aggression_margin(memory):
    """Lower M5's fold margin only when a high raise rate has support."""
    actions = memory.get("_m6_opp_actions", 0)
    raises = memory.get("_m6_raises", 0)
    if actions < 24:
        return 0.20
    lower = _wilson_lower(raises, actions - raises)
    confidence = min(1.0, actions / 80.0)
    evidence = max(0.0, min(1.0, (lower - 0.18) / 0.30)) * confidence
    return 0.20 - 0.12 * evidence


def _river_bluff_is_unsafe(obs, equity, memory):
    folds, continues = memory["_m6_river_half_response"]
    if folds + continues < 12 or Action.RAISE_HALF not in obs.raise_to:
        return False

    p_fold = _wilson_lower(folds, continues)
    my_committed = (1 if obs.is_button else 2) + sum(a.amount for a in obs.action_history if a.is_me)
    opp_committed = max(0, obs.pot - my_committed)
    check_ev = equity * obs.pot - my_committed
    new_total = obs.raise_to[Action.RAISE_HALF]
    our_add = max(0, new_total - obs.my_bet)
    opp_call = min(max(0, new_total - obs.opp_bet), obs.opp_stack)
    called_ev = equity * (obs.pot + our_add + opp_call) - my_committed - our_add
    raised_ev = -(my_committed + our_add)  # conservatively fold to a river re-raise
    robust_bet_ev = p_fold * opp_committed + (1 - p_fold) * min(called_ev, raised_ev)
    return robust_bet_ev < check_ev - 0.01 * max(1, obs.pot)


def choose_action(obs, memory):
    _observe(obs, memory)
    action = anchor.choose_action(obs, memory)
    if action == Action.FOLD and obs.street != Street.PREFLOP and Action.CHECK_CALL in obs.legal_actions and obs.to_call:
        equity = anchor.base.estimate_equity(obs)
        odds = obs.to_call / max(1, obs.pot + obs.to_call)
        if equity >= odds + _aggression_margin(memory):
            action = Action.CHECK_CALL

    if (action == Action.RAISE_HALF and obs.street == Street.RIVER
            and Action.CHECK_CALL in obs.legal_actions
            and memory["_m6_changes"] < memory["_m6_change_budget"]):
        equity = anchor.base.estimate_equity(obs)
        checked_to = any(not r.is_me and r.street == Street.RIVER and r.action == Action.CHECK_CALL
                         for r in obs.action_history)
        if checked_to and equity <= 0.25 and _river_bluff_is_unsafe(obs, equity, memory):
            action = Action.CHECK_CALL
            memory["_m6_changes"] += 1
    if action == Action.RAISE_HALF and obs.street == Street.RIVER:
        memory["_m6_pending_bluff"] = anchor.base.estimate_equity(obs) <= 0.25
    return action


def on_hand_end(result, memory):
    if memory.get("_m6_pending_bluff"):
        _record_pending(memory, not result.went_to_showdown and result.winner == "me")
    anchor.on_hand_end(result, memory)
