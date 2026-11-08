"""SPR-aware commitment thresholds and blocker-gated semi-bluffs over Talon.

Grounded in two standard pot-limit/short-stack theory ideas not otherwise
used anywhere in this repo's equity-vs-random bot family:

 - Stack-to-pot ratio (SPR) commitment. With pot-limit betting and 40bb
   effective stacks, many pots are all-in within a street or two of real
   betting. When SPR is low there is little room left to retreat on a later
   street anyway, so a call now is close to just realizing showdown equity
   and defense should widen; when SPR is high, more streets of betting
   remain and a thin call now invites a bigger bet later with the same
   hand, so defense should tighten slightly. Neither this repo's base
   equity policy (bots/m1_equity) nor Talon (bots/m5_counterplay) nor
   M5/Kestrel's pressure layers condition any threshold on SPR at all.

 - Blockers. In Omaha a semi-bluff is more credible, and more likely to
   actually fold out a better hand, when the bluffer's own hole cards
   remove combinations the opponent needs for the board's strongest
   possible holdings (a paired board rank, three-or-more of one suit, the
   top board rank for trips/a straight). Kestrel's evidence-gated semi-bluff
   (which this reuses verbatim for the gate itself) fires on fold-rate
   evidence alone; Harrier additionally requires at least one real blocker.
"""
from bots.m5_counterplay import bot as talon
from game import Action, Street

BLUFF_STREETS = (Street.TURN, Street.RIVER)
BLUFF_EQUITY = 0.375
GATE_TRIALS = 12
GATE_RATE = 0.25
SPR_LOOSE = 1.5
SPR_TIGHT = 5.0
SPR_LOOSE_SHIFT = -0.07
SPR_TIGHT_SHIFT = 0.04


def load():
    talon.load()


def new_half(config, memory):
    talon.new_half(config, memory)
    memory['_hr_trials'] = {}
    memory['_hr_folds'] = {}
    memory['_hr_pending'] = None


def _spr(obs):
    effective = min(obs.my_stack, obs.opp_stack)
    return effective / max(1, obs.pot)


def _blocker_score(obs):
    board = obs.board
    if not board:
        return 0
    board_ranks = [c >> 2 for c in board]
    board_suits = [c & 3 for c in board]
    hole_ranks = [c >> 2 for c in obs.hole_cards]
    hole_suits = [c & 3 for c in obs.hole_cards]
    score = 0
    rank_counts = {r: board_ranks.count(r) for r in set(board_ranks)}
    paired = [r for r, n in rank_counts.items() if n >= 2]
    score += sum(1 for r in hole_ranks if r in paired)
    suit_counts = {s: board_suits.count(s) for s in set(board_suits)}
    flush_suit = next((s for s, n in suit_counts.items() if n >= 3), None)
    if flush_suit is not None:
        score += sum(1 for s in hole_suits if s == flush_suit)
    top_rank = max(board_ranks)
    score += sum(1 for r in hole_ranks if r == top_rank)
    return score


def choose_action(obs, memory):
    pending = memory.get('_hr_pending')
    if pending is not None and pending[0] == obs.hand_index:
        # Facing another decision in this hand means the opponent did not
        # fold to the tracked bluff; on_hand_end covers bets that end the hand.
        street = pending[1]
        memory['_hr_trials'][street] = memory['_hr_trials'].get(street, 0) + 1
        memory['_hr_pending'] = None

    action = talon.choose_action(obs, memory)
    if obs.street == Street.PREFLOP:
        return action

    # Both refinements below cost one extra equity_vs_random sample on top of
    # what Talon already spent. Against opponents that reach many postflop
    # decisions per hand (observed in testing: m2_cfr, m1_equity,
    # equity_precise, bayes_ev), that extra cost can accumulate across a
    # 1000-hand half and approach the safety wrapper's 6.0s/half cutoff,
    # which otherwise degrades the *rest* of the half to blind check/fold.
    # Stop spending the extra sample well before that point and fall back to
    # Talon's own (already-budgeted, already-validated) action instead.
    budget_left = memory.get('_half_budget', 8.0) - memory.get('_think_s', 0.0)
    if budget_left < 3.0:
        return action

    legal = obs.legal_actions

    # SPR-aware call defense: Talon folds postflop only when to_call > 2 and
    # equity < pot-odds + 0.30. Shift that margin with SPR instead of using
    # one flat number regardless of how committed the stacks already are.
    if action == Action.FOLD and obs.to_call > 2 and Action.CHECK_CALL in legal:
        equity = talon.base.estimate_equity(obs, max_samples=48)
        odds = obs.to_call / max(1, obs.pot + obs.to_call)
        spr = _spr(obs)
        shift = SPR_LOOSE_SHIFT if spr <= SPR_LOOSE else (SPR_TIGHT_SHIFT if spr >= SPR_TIGHT else 0.0)
        if equity >= odds + max(0.0, 0.30 + shift):
            return Action.CHECK_CALL

    if (obs.street in BLUFF_STREETS and obs.to_call == 0 and action == Action.CHECK_CALL
            and Action.RAISE_HALF in legal):
        trials = memory['_hr_trials'].get(obs.street, 0)
        folds = memory['_hr_folds'].get(obs.street, 0)
        can_bluff = trials < GATE_TRIALS or (folds + 2) / (trials + 4) >= GATE_RATE
        if (can_bluff and _blocker_score(obs) >= 1
                and talon.base.estimate_equity(obs, max_samples=48) < BLUFF_EQUITY):
            memory['_hr_pending'] = (obs.hand_index, obs.street)
            return Action.RAISE_HALF
    return action


def on_hand_end(result, memory):
    pending = memory.get('_hr_pending')
    if pending is not None and pending[0] == result.hand_index:
        street = pending[1]
        memory['_hr_trials'][street] = memory['_hr_trials'].get(street, 0) + 1
        if not result.went_to_showdown and result.winner == 'me':
            memory['_hr_folds'][street] = memory['_hr_folds'].get(street, 0) + 1
        memory['_hr_pending'] = None
    talon.on_hand_end(result, memory)
