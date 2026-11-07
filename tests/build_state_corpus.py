"""Build a deterministic, stratified corpus of legal game observations.

Use: python3 tests/build_state_corpus.py --states 12000
The compressed JSONL fixture is then consumed by test_state_corpus.py.
"""
import argparse
import gzip
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import game
from game import Action


def choose(mode, obs, rng):
    legal = obs.legal_actions
    if mode == "passive":
        return Action.CHECK_CALL
    if mode == "half_pressure" and Action.RAISE_HALF in legal and rng.random() < 0.55:
        return Action.RAISE_HALF
    if mode == "pot_pressure" and Action.RAISE_POT in legal and rng.random() < 0.55:
        return Action.RAISE_POT
    if mode == "call_heavy" and Action.CHECK_CALL in legal:
        return Action.CHECK_CALL
    return rng.choice(legal)


def coverage(obs):
    legal = ",".join(action.name for action in obs.legal_actions)
    return {
        "street": obs.street.name,
        "button": "button" if obs.is_button else "big_blind",
        "facing_bet": obs.to_call > 0,
        "all_in_response": obs.to_call > 0 and len(obs.legal_actions) == 2,
        "raise_count": obs.raises_this_street,
        "legal_set": legal,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--states", type=int, default=12000)
    parser.add_argument("--seed", type=int, default=20261107)
    parser.add_argument("--out", default=str(ROOT / "tests" / "fixtures" / "decision_states.jsonl.gz"))
    args = parser.parse_args()
    target = Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    modes = ("passive", "random", "half_pressure", "pot_pressure", "call_heavy")
    counts = {"street": {}, "button": {}, "facing_bet": {}, "all_in_response": {}, "raise_count": {}, "legal_set": {}}
    states = 0
    deal_index = 0
    with gzip.open(target, "wt", encoding="utf-8", compresslevel=8) as out:
        while states < args.states:
            mode = modes[deal_index % len(modes)]
            hand = game.Game(game.make_deal(str(args.seed), deal_index), game.button_for_deal(deal_index), deal_index)
            while not hand.is_terminal and states < args.states:
                seat = hand.to_act
                obs = hand.observation(seat)
                tags = coverage(obs)
                record = {"mode": mode, "observation": obs.to_dict()}
                out.write(json.dumps(record, separators=(",", ":")) + "\n")
                states += 1
                for group, value in tags.items():
                    key = str(value)
                    counts[group][key] = counts[group].get(key, 0) + 1
                hand.apply(choose(mode, obs, rng))
            deal_index += 1
    manifest = {
        "seed": args.seed,
        "states": states,
        "deals_walked": deal_index,
        "modes": list(modes),
        "coverage": counts,
        "corpus": target.name,
    }
    target.with_name("decision_states_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))

if __name__ == "__main__":
    main()
