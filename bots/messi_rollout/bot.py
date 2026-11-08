"""messi_rollout: one-ply expected-value search instead of threshold rules.

Every other strategy this session (m5_challenger/m5_counterplay, the messi_v*
lineage, the city-engine family) decides an action by comparing a single
equity number against a chain of fixed cutoffs (fold if equity < X, raise if
equity > Y). This bot is structurally different: for every legal action it
builds an explicit, cheap one-ply rollout -- an estimated bb payoff assuming
a simple opponent-response model -- and argmaxes over those payoffs. Nothing
is a hard threshold; the decision falls out of comparing four numbers.

Opponent response model (deliberately simple, O(1), no extra equity calls):
  - CHECK_CALL / facing a bet: assume the hand resolves at showdown with our
    current equity vs a random hand (the standard pot-odds EV approximation).
  - RAISE_HALF / RAISE_POT: two branches, weighted by an estimated fold
    probability tracked per street from observed opponent behavior this half
    (falls back to a street-indexed prior with no observations yet):
      * opponent folds -> we win the pot as it stood before our raise.
      * opponent calls -> showdown EV using our equity, mildly discounted
        (a calling range is stronger than a random hand) against the pot
        that results if they call.
  - FOLD is the zero baseline every other action's marginal EV is measured
    against.
"""
from bots.common.equity import equity_vs_random
from game import Action

_FOLD_PRIOR = {
    "PREFLOP": 0.12,
    "FLOP": 0.28,
    "TURN": 0.33,
    "RIVER": 0.38,
}

_CALLED_RANGE_DISCOUNT = 0.90  # a villain who calls a raise is stronger than random


def new_half(config, memory):
    memory["_rollout_fold_obs"] = {}  # street name -> [folds, total_bets_faced]


def _street_name(obs):
    return obs.street.name if hasattr(obs.street, "name") else str(obs.street)


def _fold_prob(obs, memory, action):
    street = _street_name(obs)
    stats = memory.setdefault("_rollout_fold_obs", {})
    folds, total = stats.get(street, (0, 0))
    prior = _FOLD_PRIOR.get(street, 0.25)
    # Blend observed fold rate with the prior, weighting the prior like 6
    # pseudo-observations so a handful of real hands can move it.
    observed = (folds + prior * 6) / (total + 6)
    # Bigger relative raise -> more fold equity.
    size_mult = 1.15 if action == Action.RAISE_POT else 1.0
    p = observed * size_mult
    return min(0.65, max(0.03, p))


def _record_bet_outcome(memory, street, opponent_folded):
    stats = memory.setdefault("_rollout_fold_obs", {})
    folds, total = stats.get(street, (0, 0))
    stats[street] = (folds + (1 if opponent_folded else 0), total + 1)


def choose_action(obs, memory):
    legal = obs.legal_actions
    if len(legal) == 1:
        return legal[0]

    equity = equity_vs_random(obs.hole_cards, obs.board, samples=40)

    payoffs = {}
    if Action.FOLD in legal:
        payoffs[Action.FOLD] = 0.0

    if Action.CHECK_CALL in legal:
        call_cost = obs.to_call
        resolved_pot = obs.pot + call_cost
        payoffs[Action.CHECK_CALL] = equity * resolved_pot - call_cost

    for action in (Action.RAISE_HALF, Action.RAISE_POT):
        if action not in legal:
            continue
        raise_to = obs.raise_to[action]
        my_add = raise_to - obs.my_bet
        opp_call_add = max(0, raise_to - obs.opp_bet)
        fold_p = _fold_prob(obs, memory, action)

        fold_branch = obs.pot  # we reclaim the whole pot if they give it up
        called_pot = obs.pot + my_add + opp_call_add
        called_equity = equity * _CALLED_RANGE_DISCOUNT
        call_branch = called_equity * called_pot - my_add

        payoffs[action] = fold_p * fold_branch + (1 - fold_p) * call_branch

    best = max(payoffs, key=payoffs.get)
    memory["_rollout_last_action"] = (best, _street_name(obs))
    return best


def on_hand_end(result, memory):
    last = memory.pop("_rollout_last_action", None)
    if not last:
        return
    action, street = last
    if action in (Action.RAISE_HALF, Action.RAISE_POT):
        opponent_folded = (not result.went_to_showdown) and result.winner == "me"
        _record_bet_outcome(memory, street, opponent_folded)
