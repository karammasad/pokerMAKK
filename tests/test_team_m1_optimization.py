"""Preserve strategy semantics while removing redundant equity work."""
import gzip
import json
import random
from pathlib import Path

from bots.common.safe import wrap
from bots.m1_team_tuned.equity import equity_vs_random
from bots.m1_reference.equity import equity_vs_random as original_equity
from game import AgentConfig, Observation
from league.run import load_bot


def states():
    path = Path(__file__).parent / "fixtures/decision_states.jsonl.gz"
    with gzip.open(path, "rt") as source:
        rows = [json.loads(line)["observation"] for line in source]
    return [Observation.from_dict(row) for row in random.Random(812).sample(rows, 300)]


def test_river_optimization_preserves_exact_equity_samples():
    rng = random.Random(817)
    for _ in range(50):
        cards = rng.sample(range(36), 10)
        for count in (1, 32, 64):
            assert equity_vs_random(tuple(cards[:5]), tuple(cards[5:]), count) == original_equity(
                tuple(cards[:5]), tuple(cards[5:]), count)


def test_optimized_actions_match_frozen_reference_and_reset_memory(monkeypatch):
    active_module, reference_module = [load_bot(name) for name in ("m1_team_tuned", "m1_reference")]
    # Isolate computation changes from the deliberately tuned betting policy.
    monkeypatch.setattr(active_module, "_PARAMS", dict(reference_module._PARAMS))
    active, reference = wrap(active_module), wrap(reference_module)
    memories = [{}, {}]
    for bot, memory in zip((active, reference), memories):
        bot.new_half(AgentConfig(), memory)
    for obs in states():
        for _ in range(2):  # Repeated decisions must use the same equity.
            assert active.choose_action(obs, memories[0]) == reference.choose_action(obs, memories[1])
        assert len(memories[0].get("_m1_equities", {})) <= 4
    active.new_half(AgentConfig(), memories[0])
    assert memories[0]["_m1_equities"] == {}
    assert memories[0]["_m1_hand"] is None
    assert not any(memory.get("_fallbacks", 0) for memory in memories)


def test_equity_sparring_opponents_return_legal_actions():
    observations = states()
    for name in ("equity_balanced", "equity_tight", "equity_loose"):
        bot, memory = wrap(load_bot(name)), {}
        bot.new_half(AgentConfig(), memory)
        for obs in observations:
            assert bot.choose_action(obs, memory) in obs.legal_actions
        assert memory.get("_fallbacks", 0) == 0
