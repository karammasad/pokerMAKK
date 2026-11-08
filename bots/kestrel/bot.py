"""Talon with an evidence-gated semi-bluff on both turn and river, not turn alone.

m5_challenger already extends Talon (m5_counterplay) with a single bounded,
self-monitored bluff: when checked to on the turn with weak equity, bet,
but only while a per-half trial/fold tracker shows the bluff is actually
getting folds. This candidate applies that exact, already-validated
mechanism to the river as well, with its own independent trial/fold
counter per street so one street's results never gate the other.
"""
from bots.m5_counterplay import bot as talon
from game import Action, Street

BLUFF_STREETS = (Street.TURN, Street.RIVER)
BLUFF_EQUITY = 0.375
GATE_TRIALS = 12
GATE_RATE = 0.25


def load():
    talon.load()


def new_half(config, memory):
    talon.new_half(config, memory)
    memory['_kt_trials'] = {}
    memory['_kt_folds'] = {}
    memory['_kt_pending'] = None


def choose_action(obs, memory):
    pending = memory.get('_kt_pending')
    if pending is not None and pending[0] == obs.hand_index:
        # Facing another decision in this hand means the opponent did not
        # fold to the tracked bet; on_hand_end covers bets that end the hand.
        street = pending[1]
        memory['_kt_trials'][street] = memory['_kt_trials'].get(street, 0) + 1
        memory['_kt_pending'] = None

    action = talon.choose_action(obs, memory)
    if obs.street == Street.PREFLOP:
        return action

    legal = obs.legal_actions
    if (obs.street in BLUFF_STREETS and obs.to_call == 0 and action == Action.CHECK_CALL
            and Action.RAISE_HALF in legal):
        trials = memory['_kt_trials'].get(obs.street, 0)
        folds = memory['_kt_folds'].get(obs.street, 0)
        can_bluff = trials < GATE_TRIALS or (folds + 2) / (trials + 4) >= GATE_RATE
        if can_bluff and talon.base.estimate_equity(obs, max_samples=48) < BLUFF_EQUITY:
            memory['_kt_pending'] = (obs.hand_index, obs.street)
            return Action.RAISE_HALF
    return action


def on_hand_end(result, memory):
    pending = memory.get('_kt_pending')
    if pending is not None and pending[0] == result.hand_index:
        street = pending[1]
        memory['_kt_trials'][street] = memory['_kt_trials'].get(street, 0) + 1
        if not result.went_to_showdown and result.winner == 'me':
            memory['_kt_folds'][street] = memory['_kt_folds'].get(street, 0) + 1
        memory['_kt_pending'] = None
    talon.on_hand_end(result, memory)
