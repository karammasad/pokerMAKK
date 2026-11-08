"""Messi v11: messi_v10 with a size-dependent reraise-discipline equity bar.

Mechanism finding: v10's zoo-gate losses (and v6/v9's before it) are all to
`messi_v2`. The entire messi/v2/v6/v9/v10 family shares one mechanism in its
outer choose_action: an evidence-gated "raise the raiser" bluff that, when it
fires, is HARDCODED to Action.RAISE_HALF (never RAISE_POT) -- see every
variant's `choose_action`, `action = Action.RAISE_HALF`. It only fires when
the base policy would otherwise have folded, i.e. specifically on weak hands.

v6/v9/v10 added a defensive `_facing_reraise` rule (rr_cut): fold to any
reraise of our own bet/raise unless our equity is >=0.85, on the stated
assumption (true against City-style value-driven opponents like aguero/
ederson) that "a reraise range is usually far stronger." That assumption is
false specifically against this family's own RR bluff mechanism: when v2
reraises us via its evidence-gated RR trigger, the reraise is systematically
WEAK (by construction, it only fires on what would've been a fold) and is
always sized as RAISE_HALF. v10's flat 0.85 bar folds to those bluffs just as
readily as to a genuine strong reraise, handing messi_v2 (and any opponent
with a similar evidence-gated half-pot reraise-bluff) a reliable profit
whenever its RR trigger fires.

Fix: make the rr_cut equity bar depend on how the reraise was sized, using
information already visible in obs.action_history (no opponent-model memory,
no censored-observation problem). A RAISE_POT reraise keeps the strict 0.85
bar (pot-sized aggression is rarely how this family's bluff mechanism
manifests, and is a reasonable signal of real strength generally). A
RAISE_HALF reraise -- the family's own bluff sizing -- gets a much lower bar,
since it's a genuine mix of value and bluffs rather than reliably strong.
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


RR_CUT_EQUITY_POT = 0.85
RR_CUT_EQUITY_HALF = 0.45
STATION_MIN_MADE = 70
STATION_FOLD_RATE_MAX = 0.12
STATION_HALF_CUT = 0.355
STATION_POT_CUT = 0.745


def _facing_reraise(obs):
    recs = [r for r in obs.action_history if r.street == obs.street]
    if len(recs) >= 2 and recs[-1].action in (Action.RAISE_HALF, Action.RAISE_POT) \
            and any(r.is_me and r.action in (Action.RAISE_HALF, Action.RAISE_POT) for r in recs[:-1]):
        return recs[-1].action
    return None


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
    # Reraise discipline, size-dependent (v11 fix): the family's own RR bluff
    # is hardcoded to RAISE_HALF, so half-pot reraises need a much lower
    # equity bar than pot-sized ones to avoid folding to our own mechanism's
    # mirror image in an opponent.
    if (obs.street != Street.PREFLOP and obs.to_call > 2 and action != Action.FOLD
            and Action.FOLD in obs.legal_actions):
        reraise_action = _facing_reraise(obs)
        if reraise_action is not None:
            bar = RR_CUT_EQUITY_POT if reraise_action == Action.RAISE_POT else RR_CUT_EQUITY_HALF
            eq = attack.base.base.estimate_equity(obs, max_samples=48)
            if eq < bar:
                return Action.FOLD
    # Thin value vs a calling station (from v9/v10): if the opponent has shown
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
