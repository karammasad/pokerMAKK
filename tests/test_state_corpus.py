"""Exercise every strategy against a saved, stratified observation corpus."""
import gzip
import importlib
import json
from pathlib import Path

import game
from bots.common.safe import wrap
from league.zoo.simple import factory

ROOT = Path(__file__).resolve().parent
BOT_NAMES = ("m1_equity", "m2_cfr", "m3_exploit", "m4_learned", "m5_challenger", "random", "calling_station",
             "always_half", "always_pot", "nit", "loose_passive", "maniac", "shover", "fold_to_raise")


def make_bots():
    bots = {}
    memories = {}
    for name in BOT_NAMES:
        if name in {"m1_equity", "m2_cfr", "m3_exploit", "m4_learned", "m5_challenger"}:
            module = importlib.import_module(f"bots.{name}.bot")
            load = getattr(module, "load", None)
            if load:
                load()
        else:
            module = factory(name)
        bots[name] = wrap(module)
        memories[name] = {}
        bots[name].new_half(game.AgentConfig(), memories[name])
    return bots, memories


def test_stratified_corpus_covers_rule_and_state_edges():
    manifest = json.loads((ROOT / "fixtures" / "decision_states_manifest.json").read_text())
    coverage = manifest["coverage"]
    assert set(coverage["street"]) == {"PREFLOP", "FLOP", "TURN", "RIVER"}
    assert set(coverage["button"]) == {"button", "big_blind"}
    assert "True" in coverage["facing_bet"]
    assert "True" in coverage["all_in_response"]
    assert "4" in coverage["raise_count"]
    assert manifest["states"] >= 10000


def test_every_strategy_returns_legal_actions_on_saved_corpus():
    bots, memories = make_bots()
    corpus = ROOT / "fixtures" / "decision_states.jsonl.gz"
    with gzip.open(corpus, "rt", encoding="utf-8") as source:
        for index, line in enumerate(source):
            observation = game.Observation.from_dict(json.loads(line)["observation"])
            if index and index % 1000 == 0:
                for name, bot in bots.items():
                    memories[name] = {}
                    bot.new_half(game.AgentConfig(), memories[name])
            for name, bot in bots.items():
                action = bot.choose_action(observation, memories[name])
                assert action in observation.legal_actions, (index, name, observation, action)
