"""Research-inspired equity policy variants for controlled league comparisons.

These are distinct policy candidates around the tested evaluator/equity core,
not claimed reproductions of DeepStack, Libratus, or a full-game CFR solver.
"""
from bots.m1_equity import bot as equity_bot
from bots.common.equity import equity_vs_random
from bots.common.cards import canonical_suits
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


class FoldEquityBot:
    """Expected-value policy with a Bayesian model of fold/call/raise responses."""
    def __init__(self):
        self.prior = (2.0, 5.0, 1.0)  # modest fold rate; calls dominate; raises are possible

    def new_half(self, config, memory):
        equity_bot.load()
        equity_bot.new_half(config, memory)
        memory["_ev_counts"] = {}
        memory["_ev_hand"] = -1
        memory["_ev_seen_actions"] = 0
        memory["_ev_pending"] = None

    def _record_response(self, memory, response):
        pending = memory.get("_ev_pending")
        if pending is None:
            return
        key = f"{pending['street']}:{pending['action']}"
        counts = memory["_ev_counts"].setdefault(key, [0, 0, 0])
        counts[response] += 1
        memory["_ev_pending"] = None

    def _observe(self, obs, memory):
        if memory["_ev_hand"] != obs.hand_index:
            memory["_ev_hand"] = obs.hand_index
            memory["_ev_seen_actions"] = 0
            memory["_ev_pending"] = None
        for record in obs.action_history[memory["_ev_seen_actions"]:]:
            if record.is_me and record.action in (Action.RAISE_HALF, Action.RAISE_POT):
                memory["_ev_pending"] = {"street": record.street.name, "action": record.action.name}
            elif not record.is_me and memory.get("_ev_pending") is not None:
                response = 0 if record.action == Action.FOLD else 1 if record.action == Action.CHECK_CALL else 2
                self._record_response(memory, response)
        memory["_ev_seen_actions"] = len(obs.action_history)

    def _equity(self, obs):
        if obs.street.name == "PREFLOP" and equity_bot._PREFLOP:
            key = ";".join(f"{r}{s}" for r, s in canonical_suits(obs.hole_cards))
            value = equity_bot._PREFLOP.get(key)
            if value is not None:
                return float(value)
        return equity_bot.estimate_equity(obs)

    def _response_probs(self, obs, action, memory):
        key = f"{obs.street.name}:{action.name}"
        counts = memory["_ev_counts"].get(key, (0, 0, 0))
        values = [self.prior[i] + counts[i] for i in range(3)]
        if obs.raises_this_street >= 3:
            values[2] = 0.0
        elif obs.opp_stack <= max(0, obs.raise_to[action] - obs.opp_bet):
            values[2] = 0.0
        total = sum(values)
        return [value / total for value in values]

    def choose_action(self, obs, memory):
        self._observe(obs, memory)
        base_action = equity_bot.choose_action(obs, memory)
        if obs.to_call or not any(a in obs.legal_actions for a in (Action.RAISE_HALF, Action.RAISE_POT)):
            return base_action

        equity = self._equity(obs)
        my_committed = (1 if obs.is_button else 2) + sum(record.amount for record in obs.action_history if record.is_me)
        opp_committed = max(0, obs.pot - my_committed)
        check_ev = equity * obs.pot - my_committed
        best_action, best_ev = None, check_ev

        for action in (Action.RAISE_HALF, Action.RAISE_POT):
            if action not in obs.legal_actions:
                continue
            new_total = obs.raise_to[action]
            our_add = max(0, new_total - obs.my_bet)
            opp_call = min(max(0, new_total - obs.opp_bet), obs.opp_stack)
            call_pot = obs.pot + our_add + opp_call
            p_fold, p_call, p_raise = self._response_probs(obs, action, memory)
            call_ev = equity * call_pot - (my_committed + our_add)

            # If reraised, model a pot-sized response and continue only when its
            # showdown EV beats folding. This bounds the exploit to observed data.
            raise_ev = -(my_committed + our_add)
            opp_to_call = max(0, new_total - obs.opp_bet)
            if p_raise and obs.opp_stack > opp_to_call:
                pot_after_bet = obs.pot + our_add
                opp_raise_to = obs.opp_bet + pot_after_bet + opp_to_call
                opp_raise_add = min(max(0, opp_raise_to - obs.opp_bet), obs.opp_stack)
                extra_call = min(max(0, opp_raise_to - new_total), max(0, obs.my_stack - our_add))
                reraised_pot = pot_after_bet + opp_raise_add + extra_call
                continue_ev = equity * reraised_pot - (my_committed + our_add + extra_call)
                raise_ev = max(raise_ev, continue_ev)

            ev = p_fold * opp_committed + p_call * call_ev + p_raise * raise_ev
            if ev > best_ev:
                best_action, best_ev = action, ev

        # Store the bet so a fold/call/raise updates the right Bayesian bucket.
        if best_action is not None and best_ev > check_ev + 0.01 * max(1, obs.pot):
            memory["_ev_pending"] = {"street": obs.street.name, "action": best_action.name}
            return best_action
        if base_action in (Action.RAISE_HALF, Action.RAISE_POT) and best_action is None:
            return Action.CHECK_CALL
        return base_action

    def on_hand_end(self, result, memory):
        if memory.get("_ev_pending") is not None:
            # A showdown means the opponent continued; if we won without a
            # showdown after betting, the opponent folded.
            response = 1 if result.went_to_showdown else 0 if result.winner == "me" else 1
            self._record_response(memory, response)
        equity_bot.on_hand_end(result, memory)


def names():
    return (*PRESETS, "bayes_ev")


def factory(name):
    if name == "bayes_ev":
        return FoldEquityBot()
    if name not in PRESETS:
        raise KeyError(name)
    return PortfolioBot(name)
