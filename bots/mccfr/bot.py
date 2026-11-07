"""Runtime policy trained by bots.mccfr.train.solver."""
import json
from pathlib import Path
import random
from bots.mccfr.core import info_key
from bots.m1_equity import bot as fallback
from game import Action

TABLE = Path(__file__).parent / "tables" / "strategy.json"
_POLICY = {}


def load():
    global _POLICY
    try:
        data = json.loads(TABLE.read_text())
        _POLICY = data.get("infosets", {})
    except (OSError, ValueError):
        _POLICY = {}
    fallback.load()


def new_half(config, memory):
    if not _POLICY:
        load()
    fallback.new_half(config, memory)
    memory["_mccfr_rng"] = random.Random(20261107)


def choose_action(obs, memory):
    entry = _POLICY.get(info_key(obs))
    if not entry:
        return fallback.choose_action(obs, memory)
    probabilities = entry.get("p", ())
    legal = list(obs.legal_actions)
    weights = [max(0.0, float(probabilities[int(action)])) if int(action) < len(probabilities) else 0.0
               for action in legal]
    if not any(weights):
        return fallback.choose_action(obs, memory)
    return memory["_mccfr_rng"].choices(legal, weights=weights, k=1)[0]


def on_hand_end(result, memory):
    fallback.on_hand_end(result, memory)
