import importlib
import random

import game
from bots.common.safe import wrap
from league.zoo.simple import factory

BOT_NAMES = ["m1_equity", "m2_cfr", "m3_exploit", "m4_learned", "m5_challenger", "m5_counterplay", "random", "calling_station", "always_half", "always_pot", "nit", "loose_passive", "maniac", "shover", "fold_to_raise"]


def test_legal_actions_on_5000_observations():
    bots = {}
    memories = {}
    cfg = game.AgentConfig()
    for name in BOT_NAMES:
        mod = importlib.import_module(f"bots.{name}.bot") if name in {"m1_equity", "m2_cfr", "m3_exploit", "m4_learned", "m5_challenger", "m5_counterplay"} else factory(name)
        if name in {"m2_cfr", "m3_exploit", "m4_learned", "m5_challenger", "m5_counterplay"} and getattr(mod, "load", None):
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
