"""Exercise every strategy against a saved, stratified observation corpus."""
import gzip
import importlib
import json
from pathlib import Path

import game
from bots.common.safe import wrap
from league.zoo.simple import factory
from bots.portfolio import factory as portfolio_factory, names as portfolio_names

ROOT = Path(__file__).resolve().parent
BOT_NAMES = ('m1_equity', 'm2_cfr', 'm3_exploit', 'm4_learned', 'm5_challenger', 'm5_counterplay', 'm5_classic', 'turnblade', 'duskfox', 'nightjar', 'tidehunter', 'mirrorfin', 'm7_cherki', 'm6_safeadapt', 'm7_precision', 'm8_bayes_types', 'm9_cfrplus', 'm10_seq_cfr', 'm11_chosen', 'mccfr', 'rangefinder', 'm1_team_tuned', 'm1_reference', 'rook_fast', 'kestrel', 'haaland', 'de_bruyne', 'rodri', 'foden', 'bernardo', 'grealish', 'doku', 'stones', 'akanji', 'ederson', 'mahrez', 'gundogan', 'rangeglass', 'telltide', 'riverloom', 'suitspark', 'pebble_cfr') + (
             *portfolio_names(), "random", "calling_station", "always_half", "always_pot",
             "nit", "loose_passive", "maniac", "shover", "fold_to_raise")


def make_bots():
    bots = {}
    memories = {}
    for name in BOT_NAMES:
        if name in portfolio_names():
            module = portfolio_factory(name)
        elif name in set({'m4_learned', 'grealish', 'm1_team_tuned', 'kestrel', 'de_bruyne', 'riverloom', 'mahrez', 'm6_safeadapt', 'bernardo', 'turnblade', 'rangeglass', 'stones', 'doku', 'duskfox', 'ederson', 'm5_counterplay', 'telltide', 'rodri', 'm9_cfrplus', 'm2_cfr', 'foden', 'nightjar', 'm3_exploit', 'm7_cherki', 'mccfr', 'gundogan', 'm7_precision', 'm5_classic', 'rook_fast', 'pebble_cfr', 'm10_seq_cfr', 'mirrorfin', 'tidehunter', 'm5_challenger', 'haaland', 'm1_equity', 'rangefinder', 'm1_reference', 'm11_chosen', 'akanji', 'suitspark', 'm8_bayes_types'}):
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
