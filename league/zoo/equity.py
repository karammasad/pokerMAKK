"""Distinct equity policies for sparring, not claims of equilibrium strength.

Uses the frozen control's estimator so changes to the active bot do not change
these opponents. Each policy shares its random-range equity limitations.
"""
from bots.m1_reference import bot as reference
from bots.m1_reference.cards import canonical_suits
from game import Action, Street

POLICIES = {
    "equity_balanced": (0.70, 0.60, 0.02),
    "equity_tight": (0.82, 0.70, 0.10),
    "equity_loose": (0.64, 0.54, -0.04),
}


def factory(name):
    pot_threshold, half_threshold, margin = POLICIES[name]

    class EquityOpponent:
        def new_half(self, config, memory):
            reference.load()
            memory["equities"] = {}
            memory["hand"] = None

        def choose_action(self, obs, memory):
            if memory["hand"] != obs.hand_index:
                memory["hand"] = obs.hand_index
                memory["equities"] = {}
            key = (tuple(obs.hole_cards), tuple(obs.board))
            equity = memory["equities"].get(key)
            if equity is None:
                if obs.street == Street.PREFLOP and reference._PREFLOP:
                    canonical = ";".join(f"{r}{s}" for r, s in canonical_suits(obs.hole_cards))
                    equity = reference._PREFLOP.get(canonical)
                if equity is None:
                    equity = reference.estimate_equity(obs)
                memory["equities"][key] = equity
            legal = obs.legal_actions
            if Action.RAISE_POT in legal and equity >= pot_threshold:
                return Action.RAISE_POT
            if Action.RAISE_HALF in legal and equity >= half_threshold:
                return Action.RAISE_HALF
            odds = obs.to_call / max(1, obs.pot + obs.to_call)
            if obs.to_call == 0 or equity >= odds + margin:
                return Action.CHECK_CALL
            return Action.FOLD if Action.FOLD in legal else Action.CHECK_CALL

        def on_hand_end(self, result, memory):
            pass

    return EquityOpponent()
