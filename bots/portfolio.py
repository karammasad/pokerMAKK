"""Research-inspired equity policy variants for controlled league comparisons.

These are distinct policy candidates around the tested evaluator/equity core,
not claimed reproductions of DeepStack, Libratus, or a full-game CFR solver.
"""
from bots.m1_equity import bot as equity_bot
from bots.common.equity import equity_vs_random
from game import Action


PRESETS = {
    # Baseline threshold policy, replicated as an explicit portfolio member.
    "equity_core": dict(value_pot=0.76, value_half=0.63, margin=0.04, bluff_freq=0.0, samples=32),
    # Low variance: tighter calls and bets, useful against opponents that rarely fold.
    "equity_guarded": dict(value_pot=0.82, value_half=0.69, margin=0.075, bluff_freq=0.0, samples=32),
    # Pressure policy: thinner value thresholds and a small deterministic river bluff mix.
    "equity_pressure": dict(value_pot=0.72, value_half=0.58, margin=0.015, bluff_freq=0.045, samples=32),
    # More stable postflop equity estimates at the cost of CPU.
    "equity_precise": dict(value_pot=0.76, value_half=0.63, margin=0.04, bluff_freq=0.0, samples=96),
    # A small bounded-exploit policy: adapts only to observed action frequencies,
    # with shrinkage toward the baseline and a conservative cap on adjustments.
    "bayes_adaptive": dict(value_pot=0.76, value_half=0.63, margin=0.04, bluff_freq=0.0, samples=48),
}


class PortfolioBot:
    def __init__(self, name):
        self.name = name
        self.params = PRESETS[name]

    def new_half(self, config, memory):
        equity_bot.load()
        equity_bot.new_half(config, memory)
        memory["_portfolio_name"] = self.name
        memory["_opp_actions"] = 0
        memory["_opp_raises"] = 0
        memory["_seen_hand"] = -1
        memory["_seen_actions"] = 0

    def _observe(self, obs, memory):
        if memory.get("_seen_hand") != obs.hand_index:
            memory["_seen_hand"] = obs.hand_index
            memory["_seen_actions"] = 0
        history = obs.action_history
        start = memory.get("_seen_actions", 0)
        for action in history[start:]:
            if not action.is_me:
                memory["_opp_actions"] += 1
                if action.action in (Action.RAISE_HALF, Action.RAISE_POT):
                    memory["_opp_raises"] += 1
        memory["_seen_actions"] = len(history)

    def choose_action(self, obs, memory):
        self._observe(obs, memory)
        original_params = equity_bot._PARAMS.copy()
        original_estimator = equity_bot.estimate_equity
        equity_bot._PARAMS.update({key: self.params[key] for key in ("value_pot", "value_half", "margin", "bluff_freq")})
        equity_bot.estimate_equity = lambda state, budget_s=None, max_samples=32: equity_vs_random(
            tuple(state.hole_cards), tuple(state.board), self.params["samples"]
        )
        try:
            if self.name == "bayes_adaptive":
                n = memory["_opp_actions"]
                # Beta(2, 8) prior shrinks early estimates to modest aggression.
                raise_rate = (memory["_opp_raises"] + 2.0) / (n + 10.0)
                # Keep adaptation bounded; aggressive opponents induce wider calls,
                # passive opponents face slightly more value betting.
                shift = max(-0.035, min(0.035, (raise_rate - 0.20) * 0.16))
                equity_bot._PARAMS["margin"] = max(0.0, min(0.08, 0.04 - shift))
                equity_bot._PARAMS["value_half"] = max(0.56, min(0.70, 0.63 + shift * 0.5))
            return equity_bot.choose_action(obs, memory)
        finally:
            equity_bot._PARAMS.clear()
            equity_bot._PARAMS.update(original_params)
            equity_bot.estimate_equity = original_estimator

    def on_hand_end(self, result, memory):
        equity_bot.on_hand_end(result, memory)


def names():
    return tuple(PRESETS)


def factory(name):
    if name not in PRESETS:
        raise KeyError(name)
    return PortfolioBot(name)
