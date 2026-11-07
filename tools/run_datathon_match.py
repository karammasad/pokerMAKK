"""Run a two-half match with fresh bot servers, like the Datathon runner.

Example:
  python3 tools/run_datathon_match.py --opponent baseline_random --seed 7 --deals 1000
  python3 tools/run_datathon_match.py --opponent-script /path/to/other/agent.py \
      --opponent-name other_team --seed 7 --deals 1000
"""
import argparse
import csv
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BASELINES = (
    "baseline_random", "baseline_calling_station",
    "baseline_always_half", "baseline_always_pot",
)


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_server(port, expected, process):
    deadline = time.monotonic() + 15.0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"{expected} exited before startup (code {process.returncode})")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=0.5) as response:
                info = json.loads(response.read())
            if info.get("agent_name") == expected:
                return
        except (OSError, ValueError):
            time.sleep(0.1)
    raise TimeoutError(f"{expected} did not answer on port {port} within 15 seconds")


def stop(process):
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def play_half(half, opponent, opponent_label, our_bot, seed, deals, agent_port, opp_port, outdir, keep_logs):
    env_agent = os.environ.copy()
    env_agent["PORT"] = str(agent_port)
    env_agent["POKER_BOT"] = our_bot
    env_opp = os.environ.copy()
    env_opp["PORT"] = str(opp_port)
    env_opp["PYTHONPATH"] = os.pathsep.join(
        item for item in (str(ROOT), env_opp.get("PYTHONPATH", "")) if item
    )
    agent = subprocess.Popen([sys.executable, "agent.py"], cwd=ROOT, env=env_agent,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if opponent.startswith("script:"):
        opponent_script = Path(opponent.removeprefix("script:")).expanduser().resolve()
        opponent_cmd = [sys.executable, str(opponent_script)]
        opponent_cwd = opponent_script.parent
    else:
        opponent_cmd = [sys.executable, f"baseline-bots/{opponent}.py"]
        opponent_cwd = ROOT
    if opponent.startswith("bot:"):
        env_opp["POKER_BOT"] = opponent.removeprefix("bot:")
        opponent_cmd = [sys.executable, "agent.py"]
        opponent_cwd = ROOT
    opp = subprocess.Popen(opponent_cmd, cwd=opponent_cwd, env=env_opp,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    path = outdir / f"half{half}.json"
    try:
        wait_for_server(agent_port, our_bot, agent)
        expected = {
            "baseline_random": "RandomBot",
            "baseline_calling_station": "CallingStation",
            "baseline_always_half": "AlwaysHalf",
            "baseline_always_pot": "AlwaysPot",
        }.get(opponent, opponent_label)
        wait_for_server(opp_port, expected, opp)
        command = [
            sys.executable, "judge_engine.py", "--half", str(half),
            "--agent1", str(agent_port), "--agent2", str(opp_port),
            "--seed", str(seed), "--deals", str(deals), "--json", str(path),
        ]
        if keep_logs:
            command.append("--logs")
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=max(120, deals * 0.5))
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        print(result.stdout.strip())
    finally:
        stop(opp)
        stop(agent)
    return path


def append_league_result(opponent, seed, deals, match_result):
    """Keep fresh-server judge runs in the append-only league ledger."""
    path = ROOT / "league" / "results.csv"
    fields = ["bot", "opponent", "seed", "deals", "bb_deal", "ci_low", "ci_high", "verdict",
              "errors", "fallbacks", "think_s", "p50_ms", "p99_ms", "elapsed"]
    stats = match_result["agent_stats"]["agent1"]
    verdict = {"AGENT1_WIN": "win", "AGENT2_WIN": "loss", "CHOP": "chop"}.get(match_result["verdict"], match_result["verdict"].lower())
    row = {
        "bot": match_result.get("agent1_name", "m1_equity").split(" / ")[-1].split(" (")[0],
        "opponent": opponent.removeprefix("baseline_").removeprefix("script:").removeprefix("bot:"), "seed": seed, "deals": deals,
        "bb_deal": match_result["mean_bb_per_deal"], "ci_low": match_result["ci"][0], "ci_high": match_result["ci"][1],
        "verdict": verdict, "errors": sum(item["errors"] for item in stats), "fallbacks": "",
        "think_s": max(item["time_seconds"] for item in stats), "p50_ms": "", "p99_ms": "",
        "elapsed": match_result["elapsed_seconds"],
    }
    with path.open("a", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bot", default="m1_equity", help="our strategy from bots/ or bots.portfolio")
    opponent_group = parser.add_mutually_exclusive_group()
    opponent_group.add_argument("--opponent", choices=(*BASELINES, "all"))
    opponent_group.add_argument("--opponent-bot", help="play against another local strategy from bots/")
    opponent_group.add_argument("--opponent-script", help="path to a compatible opponent Python server script")
    parser.add_argument("--opponent-name", help="label and / health-check agent_name for --opponent-script")
    parser.add_argument("--seed", default="7", help="first reproducible match seed")
    parser.add_argument("--seeds", type=int, default=1, help="number of sequential seeds to run")
    parser.add_argument("--deals", type=int, default=1000)
    parser.add_argument("--outdir", default="/tmp/pokerMAKK-datathon")
    parser.add_argument("--logs", action="store_true", help="include full hand histories for the visual replay viewer")
    args = parser.parse_args()
    selected_opponent = args.opponent or "baseline_random"
    if args.opponent_script:
        if not args.opponent_name:
            parser.error("--opponent-name is required with --opponent-script; it must match GET / agent_name")
        script = Path(args.opponent_script).expanduser().resolve()
        if not script.is_file():
            parser.error(f"opponent script does not exist: {script}")
        opponents = (f"script:{script}",)
        labels = {opponents[0]: args.opponent_name}
    elif args.opponent_bot:
        opponents = (f"bot:{args.opponent_bot}",)
        labels = {opponents[0]: args.opponent_bot}
    else:
        opponents = BASELINES if selected_opponent == "all" else (selected_opponent,)
        labels = {}
    root_outdir = Path(args.outdir)
    root_outdir.mkdir(parents=True, exist_ok=True)
    agent_port, opp_port = free_port(), free_port()
    while opp_port == agent_port:
        opp_port = free_port()
    for opponent in opponents:
        for seed_index in range(args.seeds):
            if seed_index == 0:
                seed = args.seed
            elif args.seed.isdigit():
                seed = str(int(args.seed) + seed_index)
            else:
                seed = f"{args.seed}-{seed_index}"
            output_label = labels.get(opponent, opponent).replace("/", "_").replace(":", "_")
            outdir = root_outdir / f"{output_label}-seed-{seed}"
            outdir.mkdir(parents=True, exist_ok=True)
            halves = [
                play_half(h, opponent, labels.get(opponent, {
                    "baseline_random": "RandomBot",
                    "baseline_calling_station": "CallingStation",
                    "baseline_always_half": "AlwaysHalf",
                    "baseline_always_pot": "AlwaysPot",
                }.get(opponent, opponent)), args.bot, seed, args.deals, agent_port, opp_port, outdir, args.logs)
                for h in (1, 2)
            ]
            combined = outdir / "match.json"
            result = subprocess.run([sys.executable, "judge_engine.py", "combine", *map(str, halves), "--json", str(combined)],
                                    cwd=ROOT, text=True, capture_output=True, timeout=30)
            if result.returncode:
                raise SystemExit(result.stdout + result.stderr)
            match_result = json.loads(combined.read_text())
            append_league_result(labels.get(opponent, opponent), seed, args.deals, match_result)
            print(result.stdout.strip())
            print(f"Saved halves and combined result under {outdir}; appended to league/results.csv")

if __name__ == "__main__":
    main()
