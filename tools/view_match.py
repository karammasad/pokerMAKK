"""Create a standalone interactive hand replay from judge_engine.py JSON logs."""
import argparse
import json
from pathlib import Path
import webbrowser


PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Poker Match Replay</title>
<style>
:root{color-scheme:dark;--felt:#0e4339;--felt2:#082c27;--gold:#efc979;--ink:#eef5ef;--muted:#a7bcb4;--panel:#102722;--line:#31564a}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 50% 20%,#19584a,#081b18 76%);color:var(--ink);font:15px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;min-height:100vh}
main{max-width:1080px;margin:0 auto;padding:28px 20px 48px}.top{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin-bottom:20px}.eyebrow{color:var(--gold);letter-spacing:.16em;text-transform:uppercase;font-size:11px;font-weight:700}.title{font-size:30px;margin:4px 0 0}.score{color:var(--muted);text-align:right}.score strong{display:block;color:var(--gold);font-size:20px}
.controls,.panel{background:linear-gradient(145deg,#15342d,#10251f);border:1px solid var(--line);border-radius:16px;box-shadow:0 12px 30px #0003}.controls{padding:14px 18px;display:flex;align-items:center;gap:12px;margin-bottom:16px}.controls select,.controls button{background:#1e4036;border:1px solid #527366;color:var(--ink);border-radius:8px;padding:8px 12px;font:inherit}.controls button{cursor:pointer}.controls button:hover{border-color:var(--gold)}.controls input{flex:1;accent-color:var(--gold)}
.table{position:relative;overflow:hidden;min-height:380px;border:8px solid #4a3020;border-radius:230px;background:radial-gradient(ellipse,#18624f 0%,var(--felt) 55%,var(--felt2) 100%);box-shadow:inset 0 0 0 3px #b28b4e,0 14px 40px #0005;display:grid;grid-template-rows:1fr auto 1fr;align-items:center;padding:28px clamp(20px,7vw,78px);gap:12px}.player{display:flex;align-items:center;justify-content:center;gap:8px;flex-wrap:wrap}.player .name{min-width:125px;text-align:center;color:#e0e9e3;font-weight:650}.player .seat{font-size:11px;color:var(--muted);font-weight:400}.board{text-align:center}.cards{display:flex;gap:5px;justify-content:center;flex-wrap:wrap;min-height:57px}.card{height:54px;min-width:40px;padding:5px 6px;border-radius:7px;background:#f3f0e8;color:#202722;box-shadow:0 2px 5px #0007;display:grid;place-items:center;font:bold 20px Georgia,serif}.card.red{color:#b32f3d}.card.back{background:linear-gradient(135deg,#295a66,#172f43);color:#d4e0df;border:1px solid #8aa5a0}.board .label,.player .label{font-size:11px;color:#d3e0d8;text-transform:uppercase;letter-spacing:.13em;margin-bottom:6px}.pot{margin-top:8px;color:#f6dfab;font-weight:700}.dealer{color:var(--gold);font-size:11px;margin-left:4px}.resultline{font-size:13px;color:#d7e3dc;margin-top:8px}
.below{display:grid;grid-template-columns:1fr 1.4fr;gap:16px;margin-top:16px}.panel{padding:18px}.panel h2{margin:0 0 12px;font-size:16px;color:var(--gold)}.actions{display:flex;flex-direction:column;gap:7px;max-height:300px;overflow:auto}.action{padding:8px 10px;border-radius:8px;background:#0e211c;border:1px solid #263f36;color:#dce7e0;font-size:13px}.action b{color:#fff}.muted{color:var(--muted)}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.stat{padding:12px;background:#0e211c;border-radius:9px}.stat small{display:block;color:var(--muted);font-size:11px}.stat strong{font-size:18px}.pos{color:#9bd6a9}.neg{color:#f19f9c}.empty{color:var(--muted);text-align:center;padding:70px 10px}.foot{color:#8fa89c;font-size:12px;margin-top:13px;text-align:center}
@media(max-width:680px){.top{align-items:flex-start;flex-direction:column}.score{text-align:left}.table{border-radius:130px;min-height:340px;padding:24px 16px}.player .name{min-width:90px;font-size:12px}.card{height:45px;min-width:33px;font-size:17px}.below{grid-template-columns:1fr}.controls{flex-wrap:wrap}.controls input{min-width:60%}}
</style></head><body><main>
<div class="top"><div><div class="eyebrow">Official judge replay</div><h1 class="title">Match viewer</h1></div><div class="score" id="score"></div></div>
<div class="controls"><label for="half">Half</label><select id="half"></select><button id="prev" aria-label="Previous hand">←</button><input id="hand" type="range" min="0" value="0"><button id="next" aria-label="Next hand">→</button><span id="counter" class="muted"></span></div>
<section id="felt" class="table"></section>
<div class="below"><section class="panel"><h2>Hand result</h2><div id="result" class="stats"></div></section><section class="panel"><h2>Actions</h2><div id="actions" class="actions"></div></section></div>
<div class="foot">Private cards are shown for replay after the hand. Use this only with saved judge logs.</div></main>
<script>const match=__MATCH__;
const halfSel=document.querySelector('#half'),slider=document.querySelector('#hand');
const halfNames=['half1','half2'].filter(k=>match.logs&&match.logs[k]);
if(!halfNames.length){document.querySelector('#felt').innerHTML='<div class="empty">This result has no hand logs. Re-run with --logs to create an interactive replay.</div>';document.querySelector('.controls').style.display='none';}
function esc(x){return String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function card(c){let red=/[hd]$/.test(c);return `<span class="card ${red?'red':''}">${esc(c)}</span>`}
function amount(a){return a.amount?` ${a.amount} chips`:''}
function actionText(a){let action=a.action.replaceAll('_',' ').toLowerCase();if(a.action.startsWith('RAISE'))action+=` to ${a.street_total}`;return action+amount(a)}
function render(){if(!halfNames.length)return;const hn=halfSel.value;const list=match.logs[hn];const i=Number(slider.value);const h=list[i];const halfNo=hn==='half1'?1:2;const a1seat=match.half_totals?.[`${hn}_agent1_seat`]??(halfNo===1?0:1);const agent1seat=halfNo===1?0:1;const names=[match.agent1_name||'Agent 1',match.agent2_name||'Agent 2'];
document.querySelector('#counter').textContent=`${i+1} / ${list.length}`;
document.querySelector('#score').innerHTML=`<span>${esc(names[0])} vs ${esc(names[1])}</span><strong>${esc(match.verdict||'')}</strong><span>${Number(match.mean_bb_per_deal||0).toFixed(3)} bb/deal</span>`;
const button=h.button_seat;const net=h.nets||[0,0];const hero=agent1seat===0?0:1;
const players=[0,1].map(seat=>{let agent=seat===agent1seat?names[0]:names[1];let isButton=seat===button;return `<div class="player"><div class="name">${esc(agent)}<div class="seat">Seat ${seat}${isButton?' · BUTTON':''}</div></div><div class="cards">${h.hole_cards[seat].map(card).join('')}</div></div>`}).join('');
const board=(h.board_revealed||[]).map(card).join('');
document.querySelector('#felt').innerHTML=`${players.split('</div><div class="player">')[0]}</div><div class="board"><div class="label">Community cards</div><div class="cards">${board||'<span class="muted">No cards revealed</span>'}</div><div class="pot">Pot ${h.pot} chips</div><div class="resultline">${h.went_to_showdown?'Showdown':'Won by fold'} · button seat ${button}</div></div><div class="player">${players.split('</div><div class="player">')[1]||''}`;
const actionHtml=(h.actions||[]).map((a,n)=>`<div class="action"><b>${esc(names[a.seat===agent1seat?0:1])}</b> <span class="muted">· ${esc(a.street.toLowerCase())}</span><br>${esc(actionText(a))}</div>`).join('');
document.querySelector('#actions').innerHTML=actionHtml||'<span class="muted">No actions recorded</span>';
document.querySelector('#result').innerHTML=[0,1].map(seat=>{let agent=seat===agent1seat?names[0]:names[1];let bb=(net[seat]||0)/2;return `<div class="stat"><small>${esc(agent)} · seat ${seat}</small><strong class="${bb>0?'pos':bb<0?'neg':''}">${bb>0?'+':''}${bb.toFixed(1)} bb</strong></div>`}).join('')+`<div class="stat"><small>Hand</small><strong>${i+1}</strong></div>`;
}
for(const name of halfNames){const o=document.createElement('option');o.value=name;o.textContent=name==='half1'?'Seat 0 then 1':'Seat 1 then 0';halfSel.appendChild(o)}
halfSel.addEventListener('change',()=>{slider.max=match.logs[halfSel.value].length-1;slider.value=0;render()});slider.addEventListener('input',render);document.querySelector('#prev').onclick=()=>{slider.value=Math.max(0,+slider.value-1);render()};document.querySelector('#next').onclick=()=>{slider.value=Math.min(+slider.max,+slider.value+1);render()};
if(halfNames.length){slider.max=match.logs[halfNames[0]].length-1;render()}
</script></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("match_json", help="combined result JSON produced by judge_engine.py combine")
    parser.add_argument("--out", help="HTML output path (default beside input)")
    parser.add_argument("--open", action="store_true", help="open the generated viewer in your browser")
    args = parser.parse_args()
    source = Path(args.match_json).expanduser().resolve()
    data = json.loads(source.read_text())
    if not data.get("logs"):
        raise SystemExit("match JSON has no logs; rerun both halves with --logs and combine them")
    output = Path(args.out).expanduser().resolve() if args.out else source.with_suffix(".html")
    payload = json.dumps(data, separators=(",", ":")).replace("<", "\\u003c")
    output.write_text(PAGE.replace("__MATCH__", payload), encoding="utf-8")
    print(f"Wrote interactive replay: {output}")
    if args.open:
        webbrowser.open(output.as_uri())


if __name__ == "__main__":
    main()
