"""Range-aware postflop equity via a lightweight opponent particle filter.

Every bot in this family (m1_equity, Talon/m5_counterplay, Anchor/m5_challenger,
Kestrel, ...) estimates hand strength against a uniformly random opponent hand,
which throws away everything the betting itself reveals. Since most of the zoo
plays threshold-gated policies (bet/raise above an equity cutoff, fold below
pot odds plus a margin), every opponent action is evidence about their hand.

Osprey keeps a small set of candidate opponent hole-hands (particles) per hand,
reweights them each time the opponent acts -- using the real preflop equity
table for preflop actions (cheap, exact lookup) and a few Monte Carlo board
completions for postflop actions -- and estimates hero's equity directly
against the weighted particle set instead of against a uniform random hand.
Preflop play and the raise/fold thresholds are reused unchanged from Talon
(m5_counterplay); only what "equity" means postflop changes. A time-bank
guard and a broad try/except fall back to plain Talon so a slow or unlucky
hand can never cost more than the budget, or an error.
"""
import math
import random

from bots.common.cards import canonical_suits
from bots.common.equity import equity_vs_random
from bots.m5_counterplay import bot as talon
from evaluator import omaha_score
from game import Action, Street, BOARD_CARDS_VISIBLE

N_PARTICLES = 60
REWEIGHT_SAMPLES = 3       # board completions per particle when reweighting on a postflop action
DECISION_SAMPLES = 2       # board completions per particle when estimating hero's equity
WEIGHT_FLOOR = 0.02        # a single action can never multiply a particle's weight below this
# bots/common/safe.py's wrapper hard-caps a half at 6.0s cumulative think time and
# replaces the action with a blind check/fold past that point. Our own guard must
# trip well before that so a long half degrades to plain Talon, not check/fold.
THINK_BUDGET_GUARD_S = 1.2


def load():
    talon.load()


def new_half(config, memory):
    talon.new_half(config, memory)
    memory['_op_hand'] = None
    memory['_op_particles'] = None
    memory['_op_weights'] = None
    memory['_op_seen'] = 0


def _sigmoid(x):
    if x > 35:
        return 1.0
    if x < -35:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def _init_particles(obs, rng):
    dead = set(obs.hole_cards) | set(obs.board)
    unseen = [c for c in range(36) if c not in dead]
    if len(unseen) < 5:
        return [], []
    particles = [tuple(sorted(rng.sample(unseen, 5))) for _ in range(N_PARTICLES)]
    weights = [1.0] * len(particles)
    return particles, weights


def _reweight_action(particles, weights, record, hist_board):
    """Multiply weights in place to reflect one opponent action."""
    is_check = record.amount == 0
    preflop_table = talon._PREFLOP
    for i, particle in enumerate(particles):
        if record.street == Street.PREFLOP:
            if not preflop_table:
                continue
            key = ';'.join(f'{r}{s}' for r, s in canonical_suits(particle))
            e = preflop_table.get(key)
            if e is None:
                continue
        else:
            e = equity_vs_random(particle, hist_board, REWEIGHT_SAMPLES)
        if record.action == Action.RAISE_POT:
            mult = _sigmoid(35.0 * (e - 0.76))
        elif record.action == Action.RAISE_HALF:
            mult = _sigmoid(28.0 * (e - 0.60))
        elif is_check:
            # A check means the opponent did not clear their own bet threshold
            # (~0.375 when nothing is owed in this bot family): sharply
            # exclude, don't just mildly discount, particles above it.
            mult = 1.0 - 0.95 * _sigmoid(25.0 * (e - 0.375))
        else:  # a call: not strong enough to raise, not weak enough to fold
            mult = _sigmoid(12.0 * (e - 0.40)) * (1.0 - 0.9 * _sigmoid(20.0 * (e - 0.80)))
        weights[i] *= max(WEIGHT_FLOOR, mult)


def _sync_particles(obs, memory):
    if memory.get('_op_hand') != obs.hand_index:
        rng = random.Random((obs.hand_index * 2654435761 + sum(obs.hole_cards) * 97) & 0xFFFFFFFF)
        particles, weights = _init_particles(obs, rng)
        memory['_op_hand'] = obs.hand_index
        memory['_op_particles'] = particles
        memory['_op_weights'] = weights
        memory['_op_seen'] = 0
    particles = memory['_op_particles']
    weights = memory['_op_weights']
    if not particles:
        return particles, weights
    history = obs.action_history
    seen = memory['_op_seen']
    for idx in range(seen, len(history)):
        record = history[idx]
        if record.is_me:
            continue
        hist_board = tuple(obs.board[:BOARD_CARDS_VISIBLE[record.street]])
        _reweight_action(particles, weights, record, hist_board)
    memory['_op_seen'] = len(history)
    if sum(weights) <= 0:
        memory['_op_weights'] = weights = [1.0] * len(particles)
    return particles, weights


def _range_equity(obs, particles, weights, rng):
    hole = tuple(obs.hole_cards)
    board = tuple(obs.board)
    dead = set(hole) | set(board)
    valid = [(p, w) for p, w in zip(particles, weights) if w > 0 and not (set(p) & dead)]
    total = sum(w for _, w in valid)
    if total <= 0:
        return None
    missing = 5 - len(board)
    acc = 0.0
    if missing == 0:
        a = omaha_score(hole, board)
        for particle, w in valid:
            b = omaha_score(particle, board)
            acc += w * (1.0 if a > b else 0.5 if a == b else 0.0)
        return acc / total
    for particle, w in valid:
        local_dead = dead | set(particle)
        unseen = [c for c in range(36) if c not in local_dead]
        if len(unseen) < missing:
            continue
        wins = 0.0
        for _ in range(DECISION_SAMPLES):
            fill = rng.sample(unseen, missing)
            full_board = board + tuple(fill)
            a = omaha_score(hole, full_board)
            b = omaha_score(particle, full_board)
            wins += 1.0 if a > b else 0.5 if a == b else 0.0
        acc += w * (wins / DECISION_SAMPLES)
    return acc / total


def estimate_range_equity(obs, memory):
    """Public helper (used by tests): current range-aware equity, or None on failure."""
    particles, weights = _sync_particles(obs, memory)
    if not particles:
        return None
    rng = random.Random((obs.hand_index * 40503 + len(obs.action_history) * 977 +
                          sum(obs.hole_cards)) & 0xFFFFFFFF)
    return _range_equity(obs, particles, weights, rng)


def choose_action(obs, memory):
    if obs.street == Street.PREFLOP:
        return talon.choose_action(obs, memory)
    try:
        if memory.get('_think_s', 0.0) >= THINK_BUDGET_GUARD_S:
            raise RuntimeError('budget guard')
        equity = estimate_range_equity(obs, memory)
        if equity is None:
            raise RuntimeError('equity unavailable')
    except Exception:
        return talon.choose_action(obs, memory)
    legal = obs.legal_actions
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    if obs.to_call:
        if equity >= 0.90 and Action.RAISE_POT in legal:
            return Action.RAISE_POT
        if equity >= 0.90 and Action.RAISE_HALF in legal:
            return Action.RAISE_HALF
        if obs.to_call > 2 and equity < odds + 0.30 and Action.FOLD in legal:
            return Action.FOLD
        return Action.CHECK_CALL
    if equity >= 0.76 and Action.RAISE_POT in legal:
        return Action.RAISE_POT
    if equity >= 0.375 and Action.RAISE_HALF in legal:
        return Action.RAISE_HALF
    return Action.CHECK_CALL


def on_hand_end(result, memory):
    talon.on_hand_end(result, memory)
