import importlib
import random

import game
from bots.common.safe import wrap
from league.zoo.simple import factory

MODULE_BOTS = {'m4_learned', 'grealish', 'm1_team_tuned', 'kestrel', 'de_bruyne', 'riverloom', 'mahrez', 'm6_safeadapt', 'bernardo', 'turnblade', 'rangeglass', 'stones', 'doku', 'duskfox', 'ederson', 'm5_counterplay', 'telltide', 'rodri', 'm9_cfrplus', 'm2_cfr', 'foden', 'nightjar', 'm3_exploit', 'm7_cherki', 'mccfr', 'gundogan', 'm7_precision', 'm5_classic', 'rook_fast', 'pebble_cfr', 'undertow', 'm10_seq_cfr', 'mirrorfin', 'tidehunter', 'm5_challenger', 'haaland', 'm1_equity', 'rangefinder', 'm1_reference', 'm11_chosen', 'akanji', 'suitspark', 'm8_bayes_types'}
BOT_NAMES = ['m1_equity', 'm2_cfr', 'm3_exploit', 'm4_learned', 'm5_challenger', 'm5_counterplay', 'm5_classic', 'turnblade', 'duskfox', 'nightjar', 'tidehunter', 'mirrorfin', 'm7_cherki', 'm6_safeadapt', 'm7_precision', 'm8_bayes_types', 'm9_cfrplus', 'm10_seq_cfr', 'm11_chosen', 'mccfr', 'rangefinder', 'm1_team_tuned', 'm1_reference', 'rook_fast', 'kestrel', 'haaland', 'de_bruyne', 'rodri', 'foden', 'bernardo', 'grealish', 'doku', 'stones', 'akanji', 'ederson', 'mahrez', 'gundogan', 'rangeglass', 'telltide', 'riverloom', 'suitspark', 'pebble_cfr', 'undertow', 'random', 'calling_station', 'always_half', 'always_pot', 'nit', 'loose_passive', 'maniac', 'shover', 'fold_to_raise']


def test_legal_actions_on_5000_observations():
    bots = {}
    memories = {}
    cfg = game.AgentConfig()
    for name in BOT_NAMES:
        mod = importlib.import_module(f"bots.{name}.bot") if name in MODULE_BOTS else factory(name)
        if name in MODULE_BOTS - {"m1_equity"} and getattr(mod, "load", None):
            mod.load()
        bot = wrap(mod)
        memory = {}
        bot.new_half(cfg, memory)
        bots[name], memories[name] = bot, memory
    rng = random.Random(7)
    checked = 0
    for seed in range(2000):
        g = game.Game(game.make_deal(seed, seed), game.button_for_deal(seed), seed)
        while not g.is_terminal and checked < 5000:
            seat = g.to_act
            obs = g.observation(seat)
            # Walk diverse states while checking the active strategy and all zoo policies.
            for name, bot in bots.items():
                action = bot.choose_action(obs, memories[name])
                assert action in obs.legal_actions, (name, obs, action)
            action = rng.choice(obs.legal_actions)
            g.apply(action)
            checked += 1
    assert checked == 5000
