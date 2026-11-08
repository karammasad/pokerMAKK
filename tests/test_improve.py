from types import SimpleNamespace
from league import improve


def test_callback_errors_cannot_be_hidden_by_safety_wrapper(monkeypatch):
    def bad_callback(result,memory):
        raise RuntimeError('callback failed')
    good = SimpleNamespace(new_half=lambda c,m:None,choose_action=lambda o,m:o.legal_actions[0],on_hand_end=lambda r,m:None)
    bad = SimpleNamespace(new_half=good.new_half,choose_action=good.choose_action,on_hand_end=bad_callback)
    monkeypatch.setattr(improve.run,'load_bot',lambda name:bad if name=='bad' else good)
    row = improve.audited_match('bad','good',123,3)
    assert row['errors'] == 6
    assert row['fallbacks'] == row['opponent_fallbacks'] == 0
    assert all(a['callback_errors']==3 for a in row['audit'])


def test_improvement_gate_rejects_timing_failure_and_noisy_gain():
    rows=[]
    for seed,gain in enumerate((.3,.3,.3)):
        for name,bb in (('base',0),('next',gain)):
            rows.append(dict(bot=name,opponent='other',seed=seed,bb_deal=bb,
                             errors=0,fallbacks=0,opponent_fallbacks=0,think_s=2,opponent_think_s=2,
                             mean_decision_ms=.6,opponent_mean_decision_ms=.6,
                             max_decision_ms=10,opponent_max_decision_ms=10,
                             max_request_ms=12,opponent_max_request_ms=12))
    assert improve.compare(rows,'base','next')['recommend']
    rows[-1]['think_s']=4.1
    assert not improve.compare(rows,'base','next')['recommend']
    rows[-1]['think_s']=2
    rows[-1]['bb_deal']=-.3
    assert not improve.compare(rows,'base','next')['recommend']


def test_deadlines_and_missing_telemetry_fail_closed():
    rows=[]
    for seed in range(3):
        for name,bb in (('base',0),('next',.3)):
            rows.append(dict(bot=name,opponent='other',seed=seed,bb_deal=bb,
                             errors=0,fallbacks=0,opponent_fallbacks=0,think_s=2,opponent_think_s=2,
                             mean_decision_ms=.6,opponent_mean_decision_ms=.6,
                             max_decision_ms=10,opponent_max_decision_ms=10,
                             max_request_ms=12,opponent_max_request_ms=12))
    assert improve.compare(rows,'base','next')['recommend']
    rows[-1]['max_request_ms']=1100
    assert not improve.compare(rows,'base','next')['recommend']
    rows[-1]['max_request_ms']=12
    rows[-1]['mean_decision_ms']=3
    assert not improve.compare(rows,'base','next')['recommend']
    rows[-1]['mean_decision_ms']=.6
    del rows[-1]['opponent_think_s']
    assert not improve.compare(rows,'base','next')['recommend']


def test_callbacks_accumulate_into_next_request_envelope(monkeypatch):
    from itertools import count
    import pytest
    import game
    ticks=count()
    monkeypatch.setattr(improve,'time',SimpleNamespace(perf_counter=lambda:next(ticks)*.001))
    raw=SimpleNamespace(new_half=lambda c,m:None,choose_action=lambda o,m:o.legal_actions[0],on_hand_end=lambda r,m:None)
    checked=improve._checked(raw)
    memory={}
    checked.new_half(game.AgentConfig(),memory)
    checked.on_hand_end(None,memory)
    checked.on_hand_end(None,memory)
    g=game.Game(game.make_deal('envelope',0),0,0)
    checked.choose_action(g.observation(g.to_act),memory)
    assert memory['_audit']['max_request_s']==pytest.approx(.003)
    assert memory['_audit']['pending_callback_s']==0


def test_source_identity_includes_game_and_evaluator(tmp_path,monkeypatch):
    (tmp_path/'league').mkdir()
    (tmp_path/'bots').mkdir()
    (tmp_path/'bots/bot.py').write_text('x=1')
    (tmp_path/'game.py').write_text('x=1')
    (tmp_path/'evaluator.py').write_text('x=1')
    monkeypatch.setattr(improve,'__file__',str(tmp_path/'league/improve.py'))
    model_before=improve.bot_digest()
    runtime_before=improve.source_digest()
    (tmp_path/'evaluator.py').write_text('x=2')
    assert improve.bot_digest()==model_before
    assert improve.source_digest()!=runtime_before


def test_confirmation_requires_disjoint_seeds_and_frozen_models(tmp_path,monkeypatch):
    import json
    import pytest
    monkeypatch.setattr(improve,'bot_digest',lambda:'same-model')
    path=tmp_path/'development.json'
    path.write_text(json.dumps(dict(complete=True,phase='development',baseline='base',
                                    bot_digest='same-model',rows=[dict(bot='next',seed=10)])))
    args=SimpleNamespace(phase='confirmation',development_report=str(path),seeds=8,
                         baseline='base',candidate=['next'],seed_start=20)
    assert improve.validate_confirmation(args)
    args.seed_start=10
    with pytest.raises(ValueError,match='overlap'):
        improve.validate_confirmation(args)
    args.seed_start=20
    monkeypatch.setattr(improve,'bot_digest',lambda:'changed-model')
    with pytest.raises(ValueError,match='differ'):
        improve.validate_confirmation(args)
