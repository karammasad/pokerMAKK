"""Telltide: Bayesian bet-response EV with a conservative M5 backbone.

The posterior is keyed by street and size and is updated only from observed
responses to our bets. Until eight responses exist, the incumbent policy acts
unchanged. This is a small, bounded exploit model, not a claimed equilibrium.
"""
from bots.common.equity import equity_vs_random
from bots.m5_counterplay import bot as base
from game import Action, Street


def load():
    base.load()


def new_half(config, memory):
    base.new_half(config, memory)
    memory["_telltide_seen_hand"] = -1
    memory["_telltide_seen_actions"] = 0
    memory["_telltide_pending"] = None
    memory["_telltide_responses"] = {}


def _size(action):
    return Action(action).name


def _record_response(memory, pending, response):
    key = f"{pending[0]}:{pending[1]}"
    counts = memory["_telltide_responses"].setdefault(key, [0, 0, 0])
    counts[response] += 1  # fold, continue, raise


def _observe(obs, memory):
    if memory.get("_telltide_seen_hand") != obs.hand_index:
        memory["_telltide_seen_hand"] = obs.hand_index
        memory["_telltide_seen_actions"] = 0
    seen = memory["_telltide_seen_actions"]
    pending = memory.get("_telltide_pending")
    for record in obs.action_history[seen:]:
        if record.is_me and record.action in (Action.RAISE_HALF, Action.RAISE_POT):
            pending = (int(record.street), _size(record.action))
        elif not record.is_me and pending is not None:
            response = (0 if record.action == Action.FOLD else
                        2 if record.action in (Action.RAISE_HALF, Action.RAISE_POT) else 1)
            _record_response(memory, pending, response)
            pending = None
    memory["_telltide_seen_actions"] = len(obs.action_history)
    memory["_telltide_pending"] = pending


def _finish_action(obs, memory, action):
    if action in (Action.RAISE_HALF, Action.RAISE_POT):
        memory["_telltide_pending"] = (int(obs.street), action.name)
        memory["_telltide_seen_actions"] = len(obs.action_history)
    return action


def _bet_ev(obs, equity, action, response_probs):
    fold_p, continue_p, raise_p = response_probs
    our_add = max(0, obs.raise_to[action] - obs.my_bet)
    opp_call = min(max(0, obs.raise_to[action] - obs.opp_bet), obs.opp_stack)
    called_ev = equity * (obs.pot + our_add + opp_call) - our_add
    fold_ev = obs.pot  # our unmatched wager is returned when the opponent folds
    reraise_ev = -our_add  # robustly assume we release to another raise
    return fold_p * fold_ev + continue_p * called_ev + raise_p * reraise_ev


def choose_action(obs, memory):
    _observe(obs, memory)
    if obs.street == Street.PREFLOP or obs.to_call != 0:
        action = base.choose_action(obs, memory)
        return _finish_action(obs, memory, action)

    # On checked-to postflop decisions, compute the baseline equity once here
    # instead of calling M5 (48 samples) and then running another estimator.
    samples = 24 if memory.get("_think_s", 0.0) < 1.5 else 8
    equity = equity_vs_random(tuple(obs.hole_cards), tuple(obs.board), samples)
    current_ev = equity * obs.pot
    legal = obs.legal_actions
    if equity >= 0.76 and Action.RAISE_POT in legal:
        baseline_action = Action.RAISE_POT
    elif equity >= 0.375 and Action.RAISE_HALF in legal:
        baseline_action = Action.RAISE_HALF
    else:
        baseline_action = Action.CHECK_CALL
    best_action, best_ev = baseline_action, current_ev
    for candidate in (Action.RAISE_HALF, Action.RAISE_POT):
        if candidate not in obs.legal_actions:
            continue
        key = f"{int(obs.street)}:{candidate.name}"
        observed = memory["_telltide_responses"].get(key, [0, 0, 0])
        n = sum(observed)
        if n < 8:
            continue
        prior = (3.0, 6.0, 1.0) if candidate == Action.RAISE_HALF else (2.5, 6.5, 1.0)
        total = n + sum(prior)
        fold_p, continue_p, raise_p = ((prior[i] + observed[i]) / total for i in range(3))
        ev = _bet_ev(obs, equity, candidate, (fold_p, continue_p, raise_p))
        if ev > best_ev + 0.02 * max(1, obs.pot):
            best_action, best_ev = candidate, ev
    return _finish_action(obs, memory, best_action)


def on_hand_end(result, memory):
    pending = memory.get("_telltide_pending")
    if pending is not None:
        # A terminal hand has no later observation to record its response.
        # A no-showdown win is a fold; showdown or a non-me winner is a
        # continuation (a call or raise after our bet).
        response = 0 if result.winner == "me" and not result.went_to_showdown else 1
        _record_response(memory, pending, response)
    memory["_telltide_pending"] = None
    base.on_hand_end(result, memory)
