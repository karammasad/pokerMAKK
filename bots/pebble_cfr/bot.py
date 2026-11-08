"""PebbleCFR: compact sequence-aware MCCFR+ blueprint with safe M5 fallback.

The table is a research prototype trained over the official transitions,
with an imperfect-recall equity abstraction. It is not an equilibrium claim.
"""
import gzip
import json
from pathlib import Path
import random

from bots.m5_counterplay import bot as fallback
from bots.mccfr.core import info_key_sequence
from game import Action


TABLE = Path(__file__).parent / "tables" / "strategy.json.gz"
_POLICY = {}
MIN_VISITS = 3


def load():
    global _POLICY
    try:
        _POLICY = json.loads(gzip.decompress(TABLE.read_bytes())).get("infosets", {})
    except (OSError, ValueError, EOFError):
        _POLICY = {}
    fallback.load()


def new_half(config, memory):
    if not _POLICY:
        load()
    fallback.new_half(config, memory)
    memory["_pebble_cfr_rng"] = random.Random(20261107)


def choose_action(obs, memory):
    entry = _POLICY.get(info_key_sequence(obs))
    if not entry or int(entry.get("visits", 0)) < MIN_VISITS:
        return fallback.choose_action(obs, memory)
    probabilities = entry.get("p", ())
    legal = list(obs.legal_actions)
    weights = [max(0.0, float(probabilities[int(action)]))
               if int(action) < len(probabilities) else 0.0 for action in legal]
    if not any(weights):
        return fallback.choose_action(obs, memory)
    return memory["_pebble_cfr_rng"].choices(legal, weights=weights, k=1)[0]


def on_hand_end(result, memory):
    fallback.on_hand_end(result, memory)
