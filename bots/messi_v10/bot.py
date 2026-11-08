"""Messi v10: messi_v6 plus a much milder, higher-evidence-bar version of v9's thin-value-vs-stations rule.

Mechanism audit of bots/city_core.py (aguero/ederson's shared engine, both of
which have a validated edge over m5_challenger) found two City mechanisms not
yet in the messi lineage:
  1. `rr_cut` -- already grafted onto messi_v6.
  2. `station_thin` -- a value-side lever messi has NEVER had: when a generic
     per-half counter shows the opponent rarely folds to our bets/raises
     (made>=40 samples, fold-rate<0.20, same thresholds/formula as
     city_core._fold_rate/station_thin), lower the no-bet-facing value
     thresholds slightly (half_cut 0.375->0.335, pot_cut 0.76->0.73, the same
     deltas city_core/ederson use) so weaker hands get value-bet against a
     calling station instead of checking.

This is deliberately isolated to the VALUE side (thin-betting into stations)
and gated on a NEW, generic make/fold counter across all of our bets/raises
(not the narrow trial counters messi already has for specific bluff lines).
It does not touch bluff frequency or aggression -- those are the City traits
plain messi already beats aguero/ederson with -- to avoid reintroducing the
pattern messi punishes them for.
"""
from bots.common import counter_strategies as attack
from bots.common.cards import canonical_suits
from game import Action, Street


def load():
    attack.load()


def new_half(config, memory):
    attack.new_half(config, memory)
    memory['_st_made'] = 0
    memory['_st_folded'] = 0
    memory['_st_pending'] = False


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


RR_CUT_EQUITY = 0.85
STATION_MIN_MADE = 70
STATION_FOLD_RATE_MAX = 0.12
STATION_HALF_CUT = 0.355
STATION_POT_CUT = 0.745


def _facing_reraise(obs):
    recs = [r for r in obs.action_history if r.street == obs.street]
    return (len(recs) >= 2 and recs[-1].action in (Action.RAISE_HALF, Action.RAISE_POT)
            and any(r.is_me and r.action in (Action.RAISE_HALF, Action.RAISE_POT) for r in recs[:-1]))


def _fold_rate(memory):
    made, folded = memory.get('_st_made', 0), memory.get('_st_folded', 0)
    return (folded + 2) / (made + 6)


def _is_station(memory):
    return memory.get('_st_made', 0) >= STATION_MIN_MADE and _fold_rate(memory) < STATION_FOLD_RATE_MAX


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
    # Reraise discipline (from messi_v6): demand real equity to continue
    # against a reraise of our own bet/raise.
    if (obs.street != Street.PREFLOP and obs.to_call > 2 and action != Action.FOLD
            and Action.FOLD in obs.legal_actions and _facing_reraise(obs)):
        eq = attack.base.base.estimate_equity(obs, max_samples=48)
        if eq < RR_CUT_EQUITY:
            return Action.FOLD
    # Thin value vs a calling station (new in v9): if the opponent has shown
    # it rarely folds to our aggression, bet weaker hands for value instead
    # of checking them, mirroring city_core's station_thin lever.
    if (obs.street != Street.PREFLOP and obs.to_call == 0 and action == Action.CHECK_CALL
            and _is_station(memory)):
        eq = attack.base.base.estimate_equity(obs, max_samples=48)
        if eq >= STATION_POT_CUT and Action.RAISE_POT in obs.legal_actions:
            return Action.RAISE_POT
        if eq >= STATION_HALF_CUT and Action.RAISE_HALF in obs.legal_actions:
            return Action.RAISE_HALF
    return action


def _base_on_hand_end(result, memory):
    attack.on_hand_end(result, memory)


def _track_station(result, memory):
    if memory.get('_st_pending'):
        memory['_st_made'] = memory.get('_st_made', 0) + 1
        if not result.went_to_showdown and result.winner == 'me':
            memory['_st_folded'] = memory.get('_st_folded', 0) + 1
    memory['_st_pending'] = False


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
    if obs.street != Street.PREFLOP and action in (Action.RAISE_HALF, Action.RAISE_POT):
        memory['_st_pending'] = True
    return action


def on_hand_end(result, memory):
    if memory.get('_rr_pending') == result.hand_index:
        memory['_rr_trials'] = memory.get('_rr_trials', 0) + 1
        if not result.went_to_showdown and result.winner == 'me':
            memory['_rr_folds'] = memory.get('_rr_folds', 0) + 1
        memory['_rr_pending'] = None
    _track_station(result, memory)
    _base_on_hand_end(result, memory)
