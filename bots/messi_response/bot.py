"""Adaptive reraise discipline using observed responses across streets."""
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


RR_CUT_EQUITY_DEFAULT = 0.85
RR_CUT_MIN_TRIALS = 5


def _facing_reraise(obs):
    """We bet/raised this street and the opponent raised again: a strong range."""
    recs = [r for r in obs.action_history if r.street == obs.street]
    return (len(recs) >= 2 and recs[-1].action in (Action.RAISE_HALF, Action.RAISE_POT)
            and any(r.is_me and r.action in (Action.RAISE_HALF, Action.RAISE_POT) for r in recs[:-1]))


def _rr_cut_equity(memory):
    """Loosen the continue-bar as this opponent's observed reraise-us rate climbs."""
    trials = memory.get('_rc_trials', 0)
    reraises = memory.get('_rc_reraises', 0)
    if trials < RR_CUT_MIN_TRIALS:
        return RR_CUT_EQUITY_DEFAULT
    rate = reraises / trials
    if rate >= 0.5:
        return 0.55
    if rate >= 0.3:
        return 0.70
    return RR_CUT_EQUITY_DEFAULT


def _track_reraise_frequency(obs, memory):
    if memory.get('_rc_hand') != obs.hand_index:
        memory['_rc_hand'] = obs.hand_index
        memory['_rc_seen'] = set()
    seen = memory['_rc_seen']
    history = obs.action_history
    for i, rec in enumerate(history[:-1]):
        if (rec.street == Street.PREFLOP or rec.street in seen or not rec.is_me
                or rec.action not in (Action.RAISE_HALF, Action.RAISE_POT)):
            continue
        response = history[i + 1]
        if response.street == rec.street and not response.is_me:
            seen.add(rec.street)
            memory['_rc_trials'] = memory.get('_rc_trials', 0) + 1
            if response.action in (Action.RAISE_HALF, Action.RAISE_POT):
                memory['_rc_reraises'] = memory.get('_rc_reraises', 0) + 1
    memory['_rc_pending'] = None


def _base_choose_action(obs, memory):
    _track_reraise_frequency(obs, memory)
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
    # Reraise discipline: frequency-adaptive continue-bar (see module docstring).
    if (obs.street != Street.PREFLOP and obs.to_call > 2 and action != Action.FOLD
            and Action.FOLD in obs.legal_actions and _facing_reraise(obs)):
        eq = attack.base.base.estimate_equity(obs, max_samples=48)
        if eq < _rr_cut_equity(memory):
            return Action.FOLD
    return action


def _base_on_hand_end(result, memory):
    attack.on_hand_end(result, memory)


PROBE = 100
RR_MIN_TRIALS = 10
RR_MIN_FOLD_RATE = 0.75
RR_MAX_COST_POT_MULT = 1.0


def choose_action(obs, memory):
    if memory.get('_rr_pending') == obs.hand_index:
        memory['_rr_trials'] = memory.get('_rr_trials', 0) + 1
        memory['_rr_pending'] = None
    action = _base_choose_action(obs, memory)
    previous = any(r.is_me and r.street == obs.street and r.action in (Action.RAISE_HALF, Action.RAISE_POT) for r in obs.action_history)
    eligible = (obs.street != Street.PREFLOP and obs.to_call > 2 and not previous
                and Action.RAISE_HALF in obs.legal_actions)
    if eligible and action == Action.FOLD:
        trials, folds = memory.get('_rr_trials', 0), memory.get('_rr_folds', 0)
        cost = obs.raise_to[Action.RAISE_HALF] - obs.my_bet
        fraction = (obs.hand_index * 97 + sum(obs.hole_cards) * 31 + int(obs.street) * 101) % 100
        if (cost <= obs.pot * RR_MAX_COST_POT_MULT and fraction < PROBE and
                (trials >= RR_MIN_TRIALS and (folds + 1) / (trials + 2) >= RR_MIN_FOLD_RATE)):
            action = Action.RAISE_HALF
    if eligible and action in (Action.RAISE_HALF, Action.RAISE_POT):
        memory['_rr_pending'] = obs.hand_index
    if (obs.street != Street.PREFLOP and obs.street not in memory.get('_rc_seen', set())
            and action in (Action.RAISE_HALF, Action.RAISE_POT)):
        memory['_rc_pending'] = (obs.hand_index, obs.street)
    return action


def on_hand_end(result, memory):
    pending = memory.get('_rc_pending')
    if (pending and pending[0] == result.hand_index
            and (result.went_to_showdown or result.winner == 'me')):
        memory['_rc_trials'] = memory.get('_rc_trials', 0) + 1
    memory['_rc_pending'] = None
    if memory.get('_rr_pending') == result.hand_index:
        memory['_rr_trials'] = memory.get('_rr_trials', 0) + 1
        if not result.went_to_showdown and result.winner == 'me':
            memory['_rr_folds'] = memory.get('_rr_folds', 0) + 1
        memory['_rr_pending'] = None
    _base_on_hand_end(result, memory)
