"""Lightweight practice opponents implementing the standard bot API."""
import random
from game import Action, Street


def factory(name):
    class ZooBot:
        def new_half(self, config, memory):
            memory["rng"] = random.Random(0)

        def choose_action(self, obs, memory):
            legal = obs.legal_actions
            if name == "random":
                return memory["rng"].choice(legal)
            if name == "calling_station":
                return Action.CHECK_CALL
            if name == "always_half":
                return Action.RAISE_HALF if Action.RAISE_HALF in legal else Action.CHECK_CALL
            if name == "always_pot":
                return Action.RAISE_POT if Action.RAISE_POT in legal else Action.CHECK_CALL
            if name == "maniac":
                return Action.RAISE_POT if Action.RAISE_POT in legal else Action.CHECK_CALL
            if name == "shover":
                return Action.RAISE_POT if Action.RAISE_POT in legal and obs.street == Street.PREFLOP else (Action.FOLD if Action.FOLD in legal else Action.CHECK_CALL)
            if name == "loose_passive":
                return Action.CHECK_CALL
            if name == "nit":
                strong = sum(c >> 2 for c in obs.hole_cards) > 27
                return Action.CHECK_CALL if obs.to_call == 0 or strong else (Action.FOLD if Action.FOLD in legal else Action.CHECK_CALL)
            if name == "fold_to_raise":
                if obs.to_call > 0 and obs.raises_this_street and Action.FOLD in legal:
                    return Action.FOLD
                return Action.CHECK_CALL
            return Action.CHECK_CALL

        def on_hand_end(self, result, memory):
            pass
    return ZooBot()
