"""Feature MLP equity estimate with a safe Method 1 fallback."""
from pathlib import Path
import numpy as np
from bots.common.cards import hand_features, FEATURE_NAMES
from bots.m1_equity import bot as base

WEIGHTS = Path(__file__).parent / "weights" / "equity.npz"
_MODEL = None


def load():
    global _MODEL
    if WEIGHTS.exists():
        try:
            data = np.load(WEIGHTS)
            if "test_mae" not in data or float(data["test_mae"]) > 0.05:
                _MODEL = None
            else:
                _MODEL = tuple(data[k] for k in ("w1", "b1", "w2", "b2", "w3", "b3", "mean", "std"))
        except (OSError, ValueError, KeyError):
            _MODEL = None


def predict(obs):
    if _MODEL is None:
        return base.estimate_equity(obs)
    w1, b1, w2, b2, w3, b3, mean, std = _MODEL
    features = hand_features(obs.hole_cards, obs.board)
    x = np.array([[features[k] for k in FEATURE_NAMES]], dtype=np.float32)
    x = (x - mean) / np.maximum(std, 1e-5)
    h1 = np.tanh(x @ w1 + b1)
    h2 = np.tanh(h1 @ w2 + b2)
    return float(np.clip((h2 @ w3 + b3)[0, 0], 0.02, 0.98))


def new_half(config, memory):
    base.new_half(config, memory)


def choose_action(obs, memory):
    # Preserve the calibrated strategy decisions while the optional predictor supplies equity.
    eq = predict(obs)
    fallback = base.choose_action(obs, memory)
    odds = obs.to_call / max(1, obs.pot + obs.to_call)
    from game import Action
    if Action.CHECK_CALL in obs.legal_actions and obs.to_call and eq >= odds + 0.04:
        return Action.CHECK_CALL
    return fallback


def on_hand_end(result, memory):
    pass
