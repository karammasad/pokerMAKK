"""aguero: City engine + a cross-hand opponent model that rewrites the profile every decision.

Everything learned about the opponent in this half (all past hands) feeds the next
decision:
* per-street fold rate to our postflop bets/raises  -> pot-size bluffs against opponents who fold a lot
  (turn/river semi-bluffs keep city_core's own fold-response gate; a per-street gate was tested and cost ~0.27 bb/deal)
* preflop fold rate to our opens                    -> lighter opens against folders
* showdown reads: strength of the hands the opponent showed after betting/raising
  postflop (bluffy -> call wider, honest -> fold to re-raises more)
* showdown reads of calling range: what they called our bets with (station -> thin value, no bluffs)
* raise rate -> call-down / M5 switch vs spew (inherited from city_core, hybrid)
Per-half state lives in memory["_ag"]; no globals.
"""
from bots import city_core as core
from bots.common.equity import equity_vs_random
from game import Action, Street

BASE = {'rr_cut': 0.85, 'no_refine_s': 1.3, 'panic_s': 2.1, 'panic_samples': 10,
        'refine_samples': 80, 'band': 0.06, 'call_margin': 0.29, 'river_call_margin': 0.28,
        'aggro_mode': 'hybrid', 'aggro_rate': 0.4, 'tb_gate': True,
        'open_mix': True, 'bluff': 0.03, 'tb_turn': True, 'tb_river': True}
RAISES = (Action.RAISE_HALF, Action.RAISE_POT)


def load():
    core.load()


def new_half(config, memory):
    core.new_half(config, memory)
    memory["_ag"] = {"hand": -1, "seen": 0, "aggr": False,
                     "fold": {s: [0, 0] for s in (Street.PREFLOP, Street.FLOP, Street.TURN, Street.RIVER)},
                     "sd_aggr": [0, 0.0], "sd_call": [0, 0.0], "opp_called_big": False}


def _observe(obs, ag):
    if ag["hand"] != obs.hand_index:
        ag["hand"], ag["seen"], ag["aggr"], ag["opp_called_big"] = obs.hand_index, 0, False, False
    hist = obs.action_history
    for i in range(ag["seen"], len(hist)):
        rec = hist[i]
        prev = hist[i - 1] if i else None
        if not rec.is_me:
            if rec.street != Street.PREFLOP and rec.action in RAISES:
                ag["aggr"] = True
            if prev is not None and prev.is_me and prev.street == rec.street and prev.action in RAISES:
                t = ag["fold"][rec.street]
                t[0] += 1
                t[1] += rec.action == Action.FOLD
                if rec.action == Action.CHECK_CALL and rec.street != Street.PREFLOP:
                    ag["opp_called_big"] = True
    ag["seen"] = len(hist)


def _rate(t, prior=(1.0, 3.0)):
    return (t[1] + prior[0]) / (t[0] + prior[1])


def _profile(obs, ag, st):
    p = dict(BASE)
    street = obs.street
    # per-street bluff gating from measured fold response
    t = ag["fold"][street] if street in ag["fold"] else [0, 0]
    hot = t[0] >= 25 and _rate(t, (2.0, 4.0)) >= 0.50   # opponent folds a lot here
    if hot:
        p["bluff"] = 0.10
        p["bluff_pot"] = True
    # preflop: lighter opens vs players who fold to raises
    pf = ag["fold"][Street.PREFLOP]
    if pf[0] >= 25 and _rate(pf, (2.0, 4.0)) >= 0.45:
        p["pre_light"] = 0.20
        p["pre_open"] = 0.53
    # showdown reads of their aggression
    n, s = ag["sd_aggr"]
    if n >= 8:
        avg = s / n
        if avg <= 0.52:      # bluffy aggressor: pay them off
            p["call_margin"] = 0.24
            p["river_call_margin"] = 0.22
            p["rr_cut"] = 0.80
        elif avg >= 0.64:    # honest aggressor: respect bets
            p["call_margin"] = 0.32
            p["river_call_margin"] = 0.31
            p["rr_cut"] = 0.88
    # showdown reads of what they call with
    n, s = ag["sd_call"]
    if n >= 8 and s / n < 0.42:   # they call with junk: value bet thinner, stop bluffing
        p["half_cut"] = 0.34
        p["bluff"] = 0.0
        p["tb_turn"] = p["tb_river"] = p["tb_flop_mix"] = False
    return p


def choose_action(obs, memory):
    ag = memory["_ag"]
    _observe(obs, ag)
    return core.choose_action(_profile(obs, ag, memory["_city"]), obs, memory)


def on_hand_end(result, memory):
    ag = memory.get("_ag")
    if ag is not None and result.went_to_showdown and result.opp_hole and len(result.board) == 5:
        eq = equity_vs_random(tuple(result.opp_hole), tuple(result.board), 24)
        if ag["aggr"]:
            ag["sd_aggr"][0] += 1
            ag["sd_aggr"][1] += eq
        elif ag["opp_called_big"]:
            ag["sd_call"][0] += 1
            ag["sd_call"][1] += eq
    core.on_hand_end({}, result, memory)
