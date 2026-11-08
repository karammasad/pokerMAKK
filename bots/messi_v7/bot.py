"""Messi v7: messi_v6's reraise discipline, but frequency-adaptive.

messi_v6 grafted a flat "fold to any reraise unless equity >= 0.85" rule from
the City-engine bots. Zoo-gate + targeted validation found two real leaks from
treating that bar as universal:

  - messi_v6 breaks even or loses outright to `always_pot`/`maniac` (unselective,
    constant-aggression zoo bots): they reraise almost every street regardless
    of hand strength, so a reraise from them carries little information, yet
    v6 folds to it as if it always meant a monster.
  - messi_v6 loses a real, sizeable margin to its own sibling `messi_v2`
    (confirmed -0.4 to -1.0 bb/deal across seeds). messi_v2 raises/reraises at
    the *same* thresholds messi_v6 itself inherits from `attack.choose_action`
    (eq>=0.375 for a half-pot raise, eq>=0.76 for a pot raise) -- thresholds
    far looser than "0.85 to continue" implies. Against an opponent built on
    the same raising logic, a flat 0.85 continue-bar is simply miscalibrated:
    it demands near-nuts to call a raise that, by the mirror-image logic v6
    itself uses, didn't need to be anywhere near that strong.

Fix: track how often *this specific opponent* reraises us after we bet/raise
(a plain frequency count, no showdown/outcome data needed) and lower the
continue-equity bar as that frequency rises. A rarely-reraising opponent
(like m5_challenger, aguero, ederson -- the bots v6 was tuned against) still
gets the strict 0.85 bar, since their reraises really are selective. A
frequent reraiser (maniac, always_pot, or a mirror-match sibling with loose
raise thresholds) gets a much looser bar, since their reraises are far less
informative.
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
    """Count, once per street, whether our own bet/raise got reraised."""
    key = (obs.hand_index, obs.street)
    we_raised = any(r.is_me and r.action in (Action.RAISE_HALF, Action.RAISE_POT)
                     for r in obs.action_history if r.street == obs.street)
    if not we_raised or memory.get('_rc_seen') == key:
        return
    recs = [r for r in obs.action_history if r.street == obs.street]
    if not recs or not recs[-1].is_me:
        # Opponent has acted after our raise this street -- resolve once.
        memory['_rc_seen'] = key
        memory['_rc_trials'] = memory.get('_rc_trials', 0) + 1
        if recs and recs[-1].action in (Action.RAISE_HALF, Action.RAISE_POT):
            memory['_rc_reraises'] = memory.get('_rc_reraises', 0) + 1


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
    return action


def on_hand_end(result, memory):
    if memory.get('_rr_pending') == result.hand_index:
        memory['_rr_trials'] = memory.get('_rr_trials', 0) + 1
        if not result.went_to_showdown and result.winner == 'me':
            memory['_rr_folds'] = memory.get('_rr_folds', 0) + 1
        memory['_rr_pending'] = None
    _base_on_hand_end(result, memory)
