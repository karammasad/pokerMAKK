"""Bounded development/confirmation loop for explicitly versioned bot candidates.

Run serially. Append every game to the league ledger, expose swallowed callback
errors, identify weak matchups, and recommend a candidate only with clean,
positive matched-seed evidence. Never rewrite bot code or the entry default.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import game
from bots.common.safe import wrap
from league import run

FIELDS = ['bot','opponent','seed','deals','bb_deal','ci_low','ci_high','verdict',
          'errors','fallbacks','think_s','p50_ms','p99_ms','elapsed']
SIDE_FIELDS = ['bot','opponent','seed','deals','bb_deal','elapsed','fallbacks',
               'opponent_fallbacks','think_h1_s','think_h2_s',
               'opponent_think_h1_s','opponent_think_h2_s']


def _checked(raw):
    def new_half(config, memory):
        memory['_audit'] = {'choose_s': 0.0, 'callback_s': 0.0, 'new_s': 0.0,
                             'callback_errors': 0, 'decisions': 0, 'max_choose_s': 0.0,
                             'max_request_s': 0.0, 'pending_callback_s': 0.0}
        start = time.perf_counter()
        try:
            raw.new_half(config, memory)
        except Exception:
            memory['_audit']['callback_errors'] += 1
            raise
        finally:
            memory['_audit']['new_s'] += time.perf_counter() - start

    def choose(obs, memory):
        start = time.perf_counter()
        try:
            return raw.choose_action(obs, memory)
        finally:
            elapsed = time.perf_counter() - start
            audit = memory['_audit']
            audit['choose_s'] += elapsed
            audit['decisions'] += 1
            audit['max_choose_s'] = max(audit['max_choose_s'], elapsed)
            audit['max_request_s'] = max(audit['max_request_s'], audit['pending_callback_s'] + elapsed)
            audit['pending_callback_s'] = 0.0

    def end(result, memory):
        start = time.perf_counter()
        try:
            raw.on_hand_end(result, memory)
        except Exception:
            memory['_audit']['callback_errors'] += 1
            raise
        finally:
            elapsed = time.perf_counter() - start
            memory['_audit']['callback_s'] += elapsed
            memory['_audit']['pending_callback_s'] += elapsed
    return wrap(SimpleNamespace(new_half=new_half, choose_action=choose, on_hand_end=end))


def audited_match(bot, opponent, seed, deals=1000):
    players = [_checked(run.load_bot(name)) for name in (bot, opponent)]
    nets, errors, audits, memories = [], 0, [[], []], [[], []]
    start = time.perf_counter()
    for half in (1, 2):
        values, err, mm = run.play_half(*players, seed, half, deals)
        nets.append(values)
        errors += err
        for side in (0, 1):
            memory = mm[side if half == 1 else 1 - side]
            audit = memory['_audit']
            errors += audit['callback_errors']
            audits[side].append(dict(audit))
            memories[side].append(memory)
    paired = [(a+b)/game.BIG_BLIND for a,b in zip(*nets)]
    mean = statistics.mean(paired)
    se = statistics.stdev(paired)/math.sqrt(len(paired)) if len(paired)>1 else 0.0
    low, high = mean - 1.96*se, mean + 1.96*se
    row = dict(bot=bot, opponent=opponent, seed=seed, deals=deals, bb_deal=mean,
               ci_low=low, ci_high=high, verdict='win' if low>0 else 'loss' if high<0 else 'chop',
               errors=errors, elapsed=time.perf_counter()-start)
    for side,prefix in ((0,''),(1,'opponent_')):
        aa = audits[side]
        totals = [a['choose_s']+a['callback_s']+a['new_s'] for a in aa]
        row[prefix+'think_h1_s'], row[prefix+'think_h2_s'] = totals
        row[prefix+'think_s'] = max(totals)
        row[prefix+'fallbacks'] = sum(m.get('_fallbacks',0) for m in memories[side])
        row[prefix+'audit'] = aa
        side_ms = [v for m in memories[side] for v in m.get('_decision_ms',[])]
        row[prefix+'mean_decision_ms'] = statistics.mean(side_ms) if side_ms else 0.0
        row[prefix+'max_decision_ms'] = max(side_ms,default=0.0)
        row[prefix+'max_request_ms'] = 1000 * max(max(a['max_request_s'],a['pending_callback_s'],a['new_s']) for a in aa)
    ms = sorted(v for m in memories[0] for v in m.get('_decision_ms',[]))
    row['p50_ms'] = statistics.median(ms) if ms else 0.0
    row['p99_ms'] = ms[max(0,math.ceil(.99*len(ms))-1)] if ms else 0.0
    row['mean_decision_ms'] = statistics.mean(ms) if ms else 0.0
    row['learning'] = [m.get('_atlas_learning',{}) for m in memories[0]]
    return row


def append(row):
    for path,fields in (('league/results.csv',FIELDS),('league/results.sides.csv',SIDE_FIELDS)):
        exists = Path(path).exists() and Path(path).stat().st_size>0
        with open(path,'a',newline='') as f:
            w = csv.DictWriter(f,fields,extrasaction='ignore',lineterminator='\n')
            if not exists:
                w.writeheader()
            w.writerow(row)


def _digest(paths):
    root = Path(__file__).resolve().parents[1]
    digest = hashlib.sha256()
    for path in sorted(set(paths)):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _bot_files():
    root = Path(__file__).resolve().parents[1]
    return [p for p in (root/'bots').rglob('*') if p.is_file() and '__pycache__' not in p.parts]


def bot_digest():
    return _digest(_bot_files())


def source_digest():
    root = Path(__file__).resolve().parents[1]
    runtime = list((root/'league').rglob('*.py'))
    runtime += [root/name for name in ('game.py','evaluator.py','agent.py','judge_engine.py',
                                      'requirements.txt','requirements-dev.txt') if (root/name).exists()]
    return _digest(_bot_files()+runtime)


def validate_confirmation(args):
    if args.phase != 'confirmation':
        return None
    if not args.development_report or args.seeds < 8:
        raise ValueError('confirmation requires a development report and at least eight fresh seeds')
    development = json.loads(Path(args.development_report).read_text())
    if not development.get('complete') or development.get('phase','development') != 'development':
        raise ValueError('development report must be complete and from development seeds')
    if development['baseline'] != args.baseline:
        raise ValueError('baseline differs from development report')
    tested = {r['bot'] for r in development['rows']} - {args.baseline}
    if not set(args.candidate).issubset(tested):
        raise ValueError('candidate was not evaluated in the development report')
    if development.get('bot_digest',development.get('source_digest')) != bot_digest():
        raise ValueError('bot code/assets differ from the frozen development candidate')
    old_seeds = {int(r['seed']) for r in development['rows']}
    new_seeds = set(range(args.seed_start,args.seed_start+args.seeds))
    if old_seeds & new_seeds:
        raise ValueError('confirmation seeds overlap development seeds')
    return hashlib.sha256(Path(args.development_report).read_bytes()).hexdigest()


def compare(rows, baseline, candidate):
    by_key = {(r['bot'],r['opponent'],r['seed']):r for r in rows}
    differences = {}
    weakness = {}
    opponent_gains = {}
    clean = True
    required = ('errors','fallbacks','opponent_fallbacks','think_s','opponent_think_s',
                'mean_decision_ms','opponent_mean_decision_ms',
                'max_decision_ms','opponent_max_decision_ms',
                'max_request_ms','opponent_max_request_ms')
    for r in rows:
        measured = all(k in r and isinstance(r[k],(int,float)) and math.isfinite(r[k]) and r[k]>=0 for k in required)
        clean &= measured
        if measured:
            clean &= (r['errors']==0 and r['fallbacks']==0 and r['opponent_fallbacks']==0
                      and r['think_s']<4.0 and r['opponent_think_s']<4.0
                      and r['mean_decision_ms']<=2.0 and r['opponent_mean_decision_ms']<=2.0
                      and r['max_decision_ms']<1000 and r['opponent_max_decision_ms']<1000
                      and r['max_request_ms']<1000 and r['opponent_max_request_ms']<1000)
        if r['bot'] != candidate:
            continue
        control = by_key[(baseline,r['opponent'],r['seed'])]
        gain = r['bb_deal']-control['bb_deal']
        differences.setdefault(r['seed'],[]).append(gain)
        weakness.setdefault(r['opponent'],[]).append(r['bb_deal'])
        opponent_gains.setdefault(r['opponent'],[]).append(gain)
    # Cluster by seed: don't count the same deals against five opponents as
    # five independent experiments. Small-sample t criticals are conservative.
    gains = [statistics.mean(values) for values in differences.values()]
    n = len(gains)
    mean = statistics.mean(gains)
    critical = {2:12.706,3:4.303,4:3.182,5:2.776,6:2.571,7:2.447,8:2.365,9:2.306,10:2.262}.get(n,2.262 if n<30 else 2.045)
    se = statistics.stdev(gains)/math.sqrt(n) if n>1 else math.inf
    interval = [mean-critical*se,mean+critical*se] if n>1 else [None,None]
    means = {name:statistics.mean(values) for name,values in weakness.items()}
    opponent_gains = {name:statistics.mean(values) for name,values in opponent_gains.items()}
    return dict(candidate=candidate, clean=bool(clean), mean_gain=mean,
                opponent_gains=opponent_gains,
                seed_cluster_interval=interval, opponent_means=means,
                weakest_opponents=sorted(means,key=means.get),
                recommend=bool(clean and n>1 and interval[0]>0 and min(means.values())>=-.25
                               and min(opponent_gains.values())>=-.25))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline',default='atlas')
    p.add_argument('--candidate',required=True,action='append')
    p.add_argument('--opponents',default='aguero,messi,m5_challenger,mahrez,ederson')
    p.add_argument('--seed-start',type=int,default=12010)
    p.add_argument('--seeds',type=int,default=3)
    p.add_argument('--deals',type=int,default=1000)
    p.add_argument('--out',default='/tmp/atlas-improvement.json')
    p.add_argument('--phase',choices=('development','confirmation'),default='development')
    p.add_argument('--development-report')
    args = p.parse_args()
    if args.seeds<2 or args.deals<1:
        p.error('at least two seeds and one deal are required')
    try:
        development_digest = validate_confirmation(args)
    except ValueError as exc:
        p.error(str(exc))
    names = list(dict.fromkeys([args.baseline]+args.candidate))
    if args.baseline in args.candidate:
        p.error('candidate and baseline must be distinct')
    opponents = list(dict.fromkeys(args.opponents.split(',')))
    rows = []
    identity = source_digest()
    source_stable = True
    try:
        for opponent in opponents:
            for seed in range(args.seed_start,args.seed_start+args.seeds):
                # Alternate order to reduce consistent cache/load advantage.
                order = names if seed%2==0 else list(reversed(names))
                for name in order:
                    row = audited_match(name,opponent,seed,args.deals)
                    row['source_digest'] = identity
                    append(row)
                    rows.append(row)
                    if source_digest() != identity:
                        source_stable = False
                        raise RuntimeError('Bot source/assets changed during validation; completed rows retained, recommendation withheld')
                    print(f'{name} vs {opponent} seed={seed} {row["bb_deal"]:+.4f} bb/deal errors={row["errors"]} fallbacks={row["fallbacks"]}/{row["opponent_fallbacks"]} max_s={row["think_s"]:.3f}',flush=True)
    finally:
        # Preserve completed games even after interruption. Never turn a partial
        # run into an admission decision.
        complete = source_stable and len(rows)==len(opponents)*args.seeds*len(names)
        report = dict(complete=complete,phase=args.phase,development_report_digest=development_digest,
                      source_stable=source_stable,source_digest=identity,bot_digest=bot_digest(),baseline=args.baseline,rows=rows)
        if complete:
            report['comparisons'] = [compare([r for r in rows if r['bot'] in (args.baseline,c)],args.baseline,c) for c in args.candidate]
        Path(args.out).write_text(json.dumps(report,indent=2))
    print(json.dumps(report.get('comparisons',[]),indent=2),flush=True)
    if args.phase=='development':
        print('Development recommendations require a separately frozen fresh-seed confirmation before promotion.',flush=True)
    else:
        print('Confirmation recommendations still require the full test suite and full-zoo release checks.',flush=True)


if __name__=='__main__':
    main()
