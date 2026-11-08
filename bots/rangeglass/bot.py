"""Rangeglass: action-conditioned opponent ranges with one calibrated shrink.

The base policy is M5 Counterplay preflop. Postflop it uses a fixed 16-sample
random-hand estimate and, with enough showdown examples, a single-shrink
action-profile-conditioned range estimate. It changes more than one dimension
versus Rangefinder, so the league comparison is not a pure estimator ablation.
"""
import math
import random

from bots.common.equity import equity_vs_random
from bots.m1_equity import bot as equity_base
from bots.m5_counterplay import bot as base
from evaluator import omaha_score
from game import Action, Street


_MAX_EXAMPLES = 192
_PRIOR_STRENGTH = 16.0
_RANGE_SAMPLES = 16
_POSTFLOP_SAMPLES = 16


def load():
    base.load()


def new_half(config, memory):
    base.new_half(config, memory)
    memory["_rangeglass_examples"] = []
    memory["_rangeglass_seen_hand"] = None
    memory["_rangeglass_latest_profile"] = None
    memory["_rangeglass_profiles_seen"] = {}
    memory["_rangeglass_equity_cache"] = {}


def _profile(obs):
    """Compact public action-line features up to the current decision."""
    counts = [0] * 16
    for record in obs.action_history:
        street = int(record.street)
        actor = 0 if record.is_me else 1
        # Each street tracks our/opponent calls and raises separately.
        action_class = 1 if record.action in (Action.RAISE_HALF, Action.RAISE_POT) else 0
        index = street * 4 + actor * 2 + action_class
        counts[index] = min(3, counts[index] + 1)
    return (int(obs.street), *counts)


def _profile_weight(a, b):
    # Street and recent aggression matter most; calls provide softer evidence.
    if a[0] != b[0]:
        return 0.0
    distance = 0.0
    for i, (x, y) in enumerate(zip(a[1:], b[1:])):
        delta = abs(x - y)
        if delta:
            category = (i % 4)
            distance += delta * (1.25 if category in (1, 3) else 0.7)
    return math.exp(-0.65 * distance)


def _eligible_examples(obs, profile, examples):
    dead = set(obs.hole_cards) | set(obs.board)
    weighted = []
    for record in examples:
        hand = record["hand"]
        if dead.intersection(hand):
            continue
        weight = _profile_weight(profile, record["profile"])
        if weight >= 0.025:
            weighted.append((hand, weight))
    return weighted


def _stable_seed(hole, board, profile, weighted):
    value = 2166136261
    vals = (*hole, 37, *board, 41, *profile)
    for x in vals:
        value = ((value ^ (int(x) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    for hand, weight in weighted:
        for x in hand:
            value = ((value ^ int(x)) * 16777619) & 0xFFFFFFFF
        value = ((value ^ int(weight * 10000)) * 16777619) & 0xFFFFFFFF
    return value


def _range_equity(obs, memory, profile):
    weighted = _eligible_examples(obs, profile, memory["_rangeglass_examples"])
    effective_n = sum(weight for _, weight in weighted)
    if effective_n < 3.5:
        return None

    key = (tuple(obs.hole_cards), tuple(obs.board), profile, len(weighted),
           round(effective_n, 2))
    cache = memory.setdefault("_rangeglass_equity_cache", {})
    if key in cache:
        return cache[key]

    dead = set(obs.hole_cards) | set(obs.board)
    unseen = [card for card in range(36) if card not in dead]
    missing = 5 - len(obs.board)
    rng = random.Random(_stable_seed(obs.hole_cards, obs.board, profile, weighted))
    hands, weights = zip(*weighted)
    own_river_score = omaha_score(obs.hole_cards, obs.board) if missing == 0 else None
    score = 0.0
    for _ in range(_RANGE_SAMPLES):
        opponent = rng.choices(hands, weights=weights, k=1)[0]
        remaining = [card for card in unseen if card not in opponent]
        future = rng.sample(remaining, missing)
        full_board = tuple(obs.board) + tuple(future)
        ours = own_river_score if own_river_score is not None else omaha_score(obs.hole_cards, full_board)
        theirs = omaha_score(opponent, full_board)
        score += 1.0 if ours > theirs else 0.5 if ours == theirs else 0.0

    result = (score / _RANGE_SAMPLES, effective_n)
    cache[key] = result
    if len(cache) > 24:
        cache.pop(next(iter(cache)))
    return result


def choose_action(obs, memory):
    if memory.get("_rangeglass_seen_hand") != obs.hand_index:
        memory["_rangeglass_seen_hand"] = obs.hand_index
        memory["_rangeglass_latest_profile"] = None
        memory["_rangeglass_profiles_seen"] = {}
        memory["_rangeglass_equity_cache"].clear()

    profile = _profile(obs)
    memory["_rangeglass_latest_profile"] = profile
    memory["_rangeglass_profiles_seen"][int(obs.street)] = profile
    if obs.street == Street.PREFLOP:
        return base.choose_action(obs, memory)

    # Keep a small postflop sample budget before adding empirical range trials.
    prior_equity = equity_vs_random(tuple(obs.hole_cards), tuple(obs.board), _POSTFLOP_SAMPLES)
    legal = obs.legal_actions
    if obs.to_call <= 0:
        if prior_equity >= 0.76 and Action.RAISE_POT in legal:
            return Action.RAISE_POT
        if prior_equity >= 0.375 and Action.RAISE_HALF in legal:
            return Action.RAISE_HALF
        return Action.CHECK_CALL

    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    if prior_equity >= 0.90 and Action.RAISE_POT in legal:
        return Action.RAISE_POT
    if prior_equity >= 0.90 and Action.RAISE_HALF in legal:
        return Action.RAISE_HALF
    if obs.to_call > 2 and prior_equity < odds + 0.30 and Action.FOLD in legal:
        fallback_action = Action.FOLD
    else:
        fallback_action = Action.CHECK_CALL
    if Action.FOLD not in legal or Action.CHECK_CALL not in legal:
        return fallback_action

    estimate = _range_equity(obs, memory, profile)
    if estimate is None:
        return fallback_action
    conditioned_equity, effective_n = estimate

    # Shrink the learned range toward the same uniform prior used by the
    # baseline; action-line evidence can only change a decision gradually.
    mix = effective_n / (effective_n + _PRIOR_STRENGTH)
    equity = (1.0 - mix) * prior_equity + mix * conditioned_equity
    pot_odds = obs.to_call / max(1, obs.pot + obs.to_call)
    street_margin = {Street.FLOP: 0.09, Street.TURN: 0.065, Street.RIVER: 0.04}[obs.street]
    uncertainty = 0.12 / math.sqrt(effective_n + 1.0)
    if equity >= pot_odds + street_margin + uncertainty:
        return Action.CHECK_CALL
    return Action.FOLD


def on_hand_end(result, memory):
    profiles = memory.get("_rangeglass_profiles_seen", {})
    if not profiles and memory.get("_rangeglass_latest_profile") is not None:
        profile = memory["_rangeglass_latest_profile"]
        profiles = {profile[0]: profile}
    if result.went_to_showdown and result.opp_hole and profiles:
        board_len = len(getattr(result, "board", ()))
        terminal_street = {0: 0, 3: 1, 4: 2, 5: 3}.get(board_len, max(profiles))
        examples = memory["_rangeglass_examples"]
        for street in range(min(profiles), terminal_street + 1):
            # If the hand went all-in before a later street, carry its last
            # public action profile forward: the revealed holding is still
            # evidence for that line after the runout.
            source = profiles.get(street)
            if source is None:
                source = profiles[max(key for key in profiles if key < street)]
                source = (street, *source[1:])
            examples.append({"profile": source, "hand": tuple(result.opp_hole)})
        if len(examples) > _MAX_EXAMPLES:
            del examples[:len(examples) - _MAX_EXAMPLES]
    equity_base.on_hand_end(result, memory)
