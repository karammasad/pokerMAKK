"""Messi v4: drop the reraise-the-raiser bluff entirely (diagnostic variant).

Isolates whether the original messi's raise-the-raiser layer (L3) is helping
or hurting against m5_challenger specifically: this variant keeps the
preflop steal and river bluff layers but never converts a fold into a
bluff-reraise.
"""
from bots.common import counter_strategies as attack
from bots.common.cards import canonical_suits
from game import Action, Street


def load():
    attack.load()


def new_half(config, memory):
    attack.new_half(config, memory)


def _fast_action(obs, memory):
    if memory.get('_cs_pending') == obs.hand_index:
        memory['_cs_trials'] += 1
        memory['_cs_pending'] = None
    eq = attack.base.base.estimate_equity(obs, max_samples=8)
    legal = obs.legal_actions
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    if obs.to_call:
        if eq >= 0.90:
            for candidate in (Action.RAISE_POT, Action.RAISE_HALF):
                if candidate in legal:
                    return candidate
        if obs.to_call > 2 and eq < odds + 0.30 and Action.FOLD in legal:
            return Action.FOLD
        return Action.CHECK_CALL
    if eq >= 0.76 and Action.RAISE_POT in legal:
        return Action.RAISE_POT
    if eq >= 0.375 and Action.RAISE_HALF in legal:
        return Action.RAISE_HALF
    trials, folds = memory.get('_cs_trials', 0), memory.get('_cs_folds', 0)
    if (obs.street == Street.TURN and Action.RAISE_HALF in legal
            and (trials < 12 or (folds + 2) / (trials + 4) >= 1 / 3)):
        memory['_cs_pending'] = obs.hand_index
        return Action.RAISE_HALF
    return Action.CHECK_CALL


def _base_choose_action(obs, memory):
    if obs.street != Street.PREFLOP and memory.get('_think_s', 0.0) >= 1.5:
        return _fast_action(obs, memory)
    action = attack.choose_action(obs, memory, 'm5_challenger')
    mix = (obs.hand_index * 31 + sum(card >> 2 for card in obs.hole_cards)) % 4
    if (obs.street == Street.PREFLOP and obs.is_button and obs.raises_this_street == 0
            and action == Action.CHECK_CALL and Action.RAISE_HALF in obs.legal_actions
            and mix == 0):
        key = ';'.join(f'{r}{s}' for r, s in canonical_suits(obs.hole_cards))
        if (attack.base._PREFLOP or {}).get(key, 0.5) >= 0.50:
            return Action.RAISE_HALF
    trials = memory.get('_cs_trials', 0)
    folds = memory.get('_cs_folds', 0)
    if (obs.street == Street.RIVER and obs.to_call == 0 and mix == 0
            and action == Action.CHECK_CALL and Action.RAISE_HALF in obs.legal_actions
            and trials >= 12 and (folds + 2) / (trials + 4) >= 0.55
            and attack.base.base.estimate_equity(obs, max_samples=48) < 0.375):
        return Action.RAISE_HALF
    return action


def _base_on_hand_end(result, memory):
    attack.on_hand_end(result, memory)


def choose_action(obs, memory):
    # No raise-the-raiser layer: fold decisions stand as the base policy gives them.
    return _base_choose_action(obs, memory)


def on_hand_end(result, memory):
    _base_on_hand_end(result, memory)
