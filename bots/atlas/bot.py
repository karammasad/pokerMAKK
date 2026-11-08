"""Confidence-limited response adaptation over the Aguero/City backbone.

Observed responses, including terminal folds and calls, belong to per-half
memory. Bounds are heuristic Bayesian risk controls, not equilibrium guarantees.
"""
import math
import time

from bots.atlas import engine as core
from bots.aguero import bot as aguero
from game import Action, Street

RAISES = (Action.RAISE_HALF, Action.RAISE_POT)


def load():
    aguero.load()


def new_half(config, memory):
    aguero.new_half(config, memory)
    memory['_atlas'] = {'hand': -1, 'seen': 0, 'pending': None,
                        'responses': {}, 'callback_s': 0.0}
    memory['_atlas_eq_hand'] = None
    memory['_atlas_eq'] = {}


def _cell(st, street, action, facing=False):
    return st['responses'].setdefault((int(street), int(action), bool(facing)), [0, 0, 0])


def _bounds(cell):
    # Beta(2,4) shrinks towards the half-pot bluff break-even rate.
    n, folds, _ = cell
    a, b = folds + 2.0, n - folds + 4.0
    mean = a / (a + b)
    sd = math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1)))
    return max(0.0, mean - 1.64 * sd), min(1.0, mean + 1.64 * sd)


def _observe(obs, memory):
    st = memory['_atlas']
    if st['hand'] != obs.hand_index:
        st['hand'], st['seen'], st['pending'] = obs.hand_index, 0, None
    hist = obs.action_history
    for i in range(st['seen'], len(hist)):
        rec = hist[i]
        if not rec.is_me and i:
            prev = hist[i - 1]
            if prev.is_me and prev.street == rec.street and prev.action in RAISES:
                earlier = hist[i - 2] if i >= 2 else None
                facing = bool(earlier and earlier.street == prev.street and not earlier.is_me
                              and earlier.action in RAISES)
                cell = _cell(st, rec.street, prev.action, facing)
                cell[0] += 1
                cell[1] += rec.action == Action.FOLD
                cell[2] += rec.action in RAISES
                st['pending'] = None
    st['seen'] = len(hist)
    # Preserve Aguero's showdown/aggression model. Its fold counters are
    # replaced below by the complete response ledger, so no double counting.
    aguero._observe(obs, memory['_ag'])
    for street in Street:
        cells = [v for (s, _, _), v in st['responses'].items() if s == int(street)]
        memory['_ag']['fold'][street] = [sum(c[0] for c in cells), sum(c[1] for c in cells)]


def choose_action(obs, memory) -> Action:
    _observe(obs, memory)
    st = memory['_atlas']
    if len(obs.legal_actions) == 1:
        return obs.legal_actions[0]
    p = aguero._profile(obs, memory['_ag'], memory['_city'])
    # Keep sampling bounded early enough to include hand-end bookkeeping.
    p.update(no_refine_s=0.8, panic_s=1.6, panic_samples=8,
             cb_exploit=True, cb_margin=0.12, cb_reraise=0.90)
    if obs.street != Street.PREFLOP:
        cell = _cell(st, obs.street, Action.RAISE_HALF)
        lo, hi = _bounds(cell)
        if cell[0] >= 16:
            # Only override the established pressure policy with evidence.
            if hi < 1 / 3:
                p['tb_turn'] = p['tb_river'] = p['tb_flop_mix'] = False
                p['bluff'] = 0.0
            elif lo > 1 / 3:
                p['tb_turn'] = p['tb_river'] = True
        # Uncertain response rates never justify pot-sized pure bluffs.
        pot = _cell(st, obs.street, Action.RAISE_POT)
        if _bounds(pot)[0] <= 0.5:
            p['bluff_pot'] = False
    # Frequent reraises make a rigid 85%-equity fold threshold exploitable.
    # Require repeated observed responses; never identify an opponent by name.
    cells = [v for (street, _, facing), v in st['responses'].items()
             if street == int(obs.street) and not facing]
    n, raises = sum(c[0] for c in cells), sum(c[2] for c in cells)
    if obs.street != Street.PREFLOP and n >= 20:
        a, b = raises + 1.0, n - raises + 9.0
        mean = a / (a + b)
        lower = mean - 1.64 * math.sqrt(a * b / ((a + b) ** 2 * (a + b + 1)))
        if lower > 0.10:
            p['call_margin'] = min(p['call_margin'], 0.20)
            p['river_call_margin'] = min(p['river_call_margin'], 0.20)
            p['rr_cut'] = None
    action = core.choose_action(p, obs, memory)
    facing = bool(obs.action_history and not obs.action_history[-1].is_me
                  and obs.action_history[-1].street == obs.street
                  and obs.action_history[-1].action in RAISES)
    # A profitable pure bluff must beat folding by a margin after accounting
    # for the actual cost of calling plus raising, not just the nominal size.
    if (action == Action.FOLD and obs.street != Street.PREFLOP and facing
            and not any(r.is_me and r.street == obs.street and r.action in RAISES
                        for r in obs.action_history)):
        for candidate in (Action.RAISE_HALF, Action.RAISE_POT):
            if candidate not in obs.legal_actions:
                continue
            response = _cell(st, obs.street, candidate, True)
            cost = obs.raise_to[candidate] - obs.my_bet
            breakeven = cost / max(1, obs.pot + cost)
            if response[0] >= 16 and _bounds(response)[0] > breakeven + 0.04:
                action = candidate
                memory['_city']['pending'] = True
                break
    if action in RAISES:
        st['pending'] = (obs.hand_index, obs.street, action, facing)
    return action if action in obs.legal_actions else obs.legal_actions[0]


def on_hand_end(result, memory):
    start = time.perf_counter()
    st = memory['_atlas']
    pending = st['pending']
    if pending is not None and pending[0] == result.hand_index:
        _, street, action, facing = pending
        cell = _cell(st, street, action, facing)
        cell[0] += 1
        folded = not result.went_to_showdown and result.winner == 'me'
        cell[1] += folded
        # No later decision after our raise means an opponent call at showdown.
        if result.went_to_showdown and street != Street.PREFLOP:
            memory['_ag']['opp_called_big'] = True
        st['pending'] = None
    aguero.on_hand_end(result, memory)
    elapsed = time.perf_counter() - start
    st['callback_s'] += elapsed
    # The shared wrapper times decisions only; charge callbacks as well.
    memory['_think_s'] = memory.get('_think_s', 0.0) + elapsed
