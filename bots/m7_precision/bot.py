"""M5 decision policy with sequential equity refinement near action boundaries."""
from bots.m1_equity import bot as base
from bots.common.cards import canonical_suits
from bots.common.equity import equity_vs_random
from game import Action, Street


def load():
    base.load()


def new_half(config, memory):
    base.new_half(config, memory)
    memory["_m7_decisions"] = 0
    memory["_m7_refinements_96"] = 0


def _preflop_equity(obs):
    if base._PREFLOP:
        key = ";".join(f"{r}{s}" for r, s in canonical_suits(obs.hole_cards))
        value = base._PREFLOP.get(key)
        if value is not None:
            return float(value)
    ranks = [card >> 2 for card in obs.hole_cards]
    suits = [card & 3 for card in obs.hole_cards]
    rank_counts = [ranks.count(rank) for rank in set(ranks)]
    pairs = sum(n * (n - 1) // 2 for n in rank_counts)
    gaps = sorted(set(ranks))
    connected = sum(1 for a, b in zip(gaps, gaps[1:]) if b - a <= 2)
    suit_pairs = sum(n * (n - 1) // 2 for n in [suits.count(suit) for suit in set(suits)])
    strength = 0.36 + 0.035 * pairs + 0.025 * connected + 0.018 * suit_pairs + 0.008 * sum(ranks)
    return min(0.74, max(0.24, strength))


def _decision_thresholds(obs):
    if obs.street == Street.PREFLOP:
        return ()
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    position = 0.02 if obs.is_button else 0.0
    thresholds = [base._PARAMS["value_pot"] - position,
                  base._PARAMS["value_half"] - position,
                  odds + base._PARAMS["margin"]]
    if obs.to_call > 2 and Action.FOLD in obs.legal_actions:
        thresholds.append(odds + 0.20)
    if (obs.street == Street.RIVER and obs.to_call == 0 and Action.RAISE_HALF in obs.legal_actions
            and any(not record.is_me and record.street == Street.RIVER
                    and record.action == Action.CHECK_CALL for record in obs.action_history)):
        thresholds.append(0.25)
    return tuple(thresholds)


def _equity(obs, memory):
    if obs.street == Street.PREFLOP:
        return _preflop_equity(obs)
    hole, board = tuple(obs.hole_cards), tuple(obs.board)
    samples = 32
    estimate = equity_vs_random(hole, board, samples)
    thresholds = _decision_thresholds(obs)
    # Keep the refinement band narrow: the tournament has a strict cumulative
    # time bank, and most decisions should stay at the M5 32-sample budget.
    if thresholds and min(abs(estimate - threshold) for threshold in thresholds) <= 0.06:
        samples = 96
        estimate = equity_vs_random(hole, board, samples)
        memory["_m7_refinements_96"] += 1
    return estimate


def choose_action(obs, memory):
    memory["_m7_decisions"] += 1
    equity = _equity(obs, memory)
    legal = obs.legal_actions
    if obs.street != Street.PREFLOP:
        odds = obs.to_call / max(1, obs.pot + obs.to_call)
    else:
        odds = obs.to_call / max(1, obs.pot + obs.to_call)

    # Mirror the tested M1 action rule with one shared, refined estimate.
    if obs.street == Street.RIVER and obs.to_call == 0 and Action.RAISE_HALF in legal:
        checked_to = any(not record.is_me and record.street == Street.RIVER
                         and record.action == Action.CHECK_CALL for record in obs.action_history)
        if checked_to and base._PARAMS["bluff_freq"] > 0:
            draw = (obs.hand_index * 97 + sum(obs.hole_cards) * 31) % 10000 / 10000
            if draw < base._PARAMS["bluff_freq"]:
                return Action.RAISE_HALF

    value_pot = base._PARAMS["value_pot"] - (0.02 if obs.is_button else 0.0)
    value_half = base._PARAMS["value_half"] - (0.02 if obs.is_button else 0.0)
    if Action.RAISE_POT in legal and equity >= value_pot:
        action = Action.RAISE_POT
    elif Action.RAISE_HALF in legal and equity >= value_half:
        action = Action.RAISE_HALF
    elif Action.CHECK_CALL in legal and (obs.to_call == 0 or equity >= odds + base._PARAMS["margin"]):
        action = Action.CHECK_CALL
    elif Action.FOLD in legal:
        action = Action.FOLD
    else:
        action = Action.CHECK_CALL

    # Preserve M5's two tested postflop adjustments.
    if (obs.street != Street.PREFLOP and obs.to_call > 2 and action == Action.CHECK_CALL
            and Action.FOLD in legal and equity < odds + 0.20):
        return Action.FOLD
    if (obs.street == Street.RIVER and obs.to_call == 0 and action == Action.CHECK_CALL
            and Action.RAISE_HALF in legal
            and any(not record.is_me and record.street == Street.RIVER
                    and record.action == Action.CHECK_CALL for record in obs.action_history)
            and equity <= 0.25):
        return Action.RAISE_HALF
    return action


def on_hand_end(result, memory):
    base.on_hand_end(result, memory)
