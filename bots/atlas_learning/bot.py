"""Atlas with bounded, outcome-based learning for marginal terminal river calls.

Each observed terminal call has an exact comparison with folding: its showdown
share minus the call price. Other hands never become invented counterfactual
training examples. All learning resets at each half.
"""
import math
import time

from bots.atlas import bot as base
from bots.atlas.equity import estimate
from game import Action, Street

WINDOW = 32
MIN_TRIALS = 8
PROBE_EVERY = 8


def load():
    base.load()


def new_half(config, memory):
    base.new_half(config, memory)
    memory['_atlas_learning'] = {'pending': None, 'cells': {}, 'blocked': 0,
                                  'probes': 0, 'opportunities': 0}


def _cell(state, price, reraise=True):
    # Coarse price bins avoid pretending sparse observations identify a full range.
    return state['cells'].setdefault(f'{int(bool(reraise))}:{int(price >= 0.30)}', {'outcomes': [], 'blocked': 0})


def _unprofitable(cell, current_price):
    outcomes = cell['outcomes']
    if len(outcomes) < MIN_TRIALS:
        return False
    wins = sum(share for share, _ in outcomes)
    a, b = wins + 1.0, len(outcomes) - wins + 1.0
    mean = a / (a + b)
    upper = min(1.0, mean + 1.64 * math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1))))
    price = sum(p for _, p in outcomes) / len(outcomes)
    return upper < min(price, current_price) - 0.02


def choose_action(obs, memory) -> Action:
    action = base.choose_action(obs, memory)
    state = memory['_atlas_learning']
    if not (obs.street == Street.RIVER and obs.to_call > 2
            and action == Action.CHECK_CALL and Action.FOLD in obs.legal_actions):
        return action
    # Protect high-value calls and avoid computing an estimate for forced moves.
    samples = 8 if memory.get('_think_s', 0.0) >= 1.6 else 32
    eq = estimate(obs, memory, samples)
    if eq >= 0.85:
        return action
    price = obs.to_call / max(1, obs.pot + obs.to_call)
    reraise = base.core._facing_reraise(obs)
    cell = _cell(state, price, reraise)
    state['opportunities'] += 1
    if _unprofitable(cell, price):
        cell['blocked'] += 1
        # Limited probes permit recovery if an opponent changes strategy, while
        # never forcing additional calls beyond the original Atlas policy.
        probe = cell['blocked'] % PROBE_EVERY == 0 and obs.to_call <= 8 * obs.big_blind
        if not probe:
            state['blocked'] += 1
            return Action.FOLD
        state['probes'] += 1
    state['pending'] = (obs.hand_index, price, reraise)
    return action


def on_hand_end(result, memory):
    start = time.perf_counter()
    state = memory['_atlas_learning']
    pending = state['pending']
    if pending is not None and pending[0] == result.hand_index:
        # A river call ends the betting. Only a real exposed
        # showdown can update this model; no guessed folded-card strengths.
        if result.went_to_showdown:
            share = 1.0 if result.winner == 'me' else 0.5 if result.winner == 'split' else 0.0
            cell = _cell(state, pending[1], pending[2])
            cell['outcomes'].append((share, pending[1]))
            del cell['outcomes'][:-WINDOW]
        state['pending'] = None
    # Charge this layer separately; base already charges its own hand-end work.
    elapsed = time.perf_counter() - start
    memory['_think_s'] = memory.get('_think_s', 0.0) + elapsed
    base.on_hand_end(result, memory)
