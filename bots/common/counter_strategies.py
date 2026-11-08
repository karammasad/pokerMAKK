"""Fast pressure policies and per-half opponent-response tracking."""
from bots.common.cards import canonical_suits
from bots.m5_counterplay import bot as base
from game import Action, Street


def load():
    base.load()


def new_half(config, memory):
    base.new_half(config, memory)
    memory['_cs_trials'] = 0
    memory['_cs_folds'] = 0
    memory['_cs_pending'] = None


def choose_action(obs, memory, profile):
    pending = memory.get('_cs_pending')
    if pending is not None and pending == obs.hand_index:
        # A further decision in this hand means the opponent did not fold to
        # the tracked bet; on_hand_end covers bets that end the hand directly.
        memory['_cs_trials'] = memory.get('_cs_trials', 0) + 1
        memory['_cs_pending'] = None
    action = base.choose_action(obs, memory)
    if obs.street == Street.PREFLOP:
        if (profile == 'tidehunter' and obs.is_button and obs.raises_this_street == 0
                and action == Action.CHECK_CALL and Action.RAISE_HALF in obs.legal_actions):
            key = ';'.join(f'{r}{s}' for r, s in canonical_suits(obs.hole_cards))
            equity = (base._PREFLOP or {}).get(key, 0.5)
            mix = (obs.hand_index * 31 + sum(card >> 2 for card in obs.hole_cards)) % 4
            if equity >= 0.50 and mix == 0:
                return Action.RAISE_HALF
        return action

    eligible = (obs.street == Street.TURN or
                (profile in ('duskfox', 'nightjar') and obs.street == Street.RIVER) or
                (profile == 'nightjar' and obs.street == Street.FLOP))
    if profile == 'nightjar' and obs.street != Street.TURN:
        eligible = eligible and (obs.hand_index * 31 + sum(card >> 2 for card in obs.hole_cards)) % 4 == 0
    if (eligible and obs.to_call == 0 and action == Action.CHECK_CALL
            and Action.RAISE_HALF in obs.legal_actions):
        trials = memory.get('_cs_trials', 0)
        folds = memory.get('_cs_folds', 0)
        can_bluff = profile != 'm5_challenger' or trials < 12 or (folds + 2) / (trials + 4) >= 1 / 3
        if can_bluff and base.base.estimate_equity(obs, max_samples=48) < 0.375:
            if profile == 'm5_challenger':
                memory['_cs_pending'] = obs.hand_index
            return Action.RAISE_HALF
    if profile == 'mirrorfin' and obs.street == Street.RIVER and action == Action.FOLD and Action.CHECK_CALL in obs.legal_actions:
        equity = base.base.estimate_equity(obs, max_samples=48)
        odds = obs.to_call / max(1, obs.pot + obs.to_call)
        if equity >= odds + 0.28:
            return Action.CHECK_CALL
    return action


def on_hand_end(result, memory):
    if memory.get('_cs_pending') == result.hand_index:
        memory['_cs_trials'] = memory.get('_cs_trials', 0) + 1
        if not result.went_to_showdown and result.winner == 'me':
            memory['_cs_folds'] = memory.get('_cs_folds', 0) + 1
        memory['_cs_pending'] = None
    base.on_hand_end(result, memory)
