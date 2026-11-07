# pokerMAKK: build instructions for Codex

You are setting up and building our team's bot for the TAMU Datathon Heads Up Poker Bot Challenge
(Short Deck 5-card PLO, heads-up). Work through the phases in order. After each phase, run the
checks listed, commit, and push. Do not skip checks. If a check fails, fix it before moving on.

Our GitHub repo: `pokerMAKK` (remote URL: `https://github.com/karammasad/pokerMAKK.git`)
Starter code: https://github.com/tamu-datathon-org/heads-up-bundle

---

## 0. Facts you must respect (from the participant guide and starter)

- Game: 36-card short deck (6 through A). Each player gets 5 hole cards; a hand uses **exactly 2 hole + 3 board**.
  Flush beats full house; trips beat a straight; A-6-7-8-9 is the lowest straight. Always score hands with
  `evaluator.omaha_score`; never write a separate evaluator.
- Stacks reset to 80 chips (40 big blinds) every hand. Blinds 1/2. Actions: FOLD, CHECK_CALL, RAISE_HALF,
  RAISE_POT. Max 4 raises per street.
- Match: 1,000 duplicate deals x 2 halves with seats swapped. Each half runs in a **fresh server**; `memory`
  is wiped between halves.
- Scoring: 95% interval of bb/deal above 0 is a win, touching 0 a chop, below 0 a loss.
- Time: 8 s bank per half, 1 s max per request. Empty bank means automatic check/fold.
  **Target: about 2 ms per decision on average, under 4 s of thinking per half.**
- 5 errors in a half is a forfeit = match loss.
- Startup (imports + `warmup()`) must finish within 15 s. Runtime: 1 CPU, 4 GB RAM, no internet,
  only `/tmp` is writable. Base image has numpy and CPU torch.
- `agent.py` and `requirements.txt` stay at the repo root. Do not change the FastAPI/uvicorn versions.
- No file over 100 MB. No Git LFS (LFS files are not downloaded by the build).

---

## 1. Repo setup

1. Clone the starter into the current folder and point it at our repo:
   ```sh
   git clone https://github.com/tamu-datathon-org/heads-up-bundle.git pokerMAKK
   cd pokerMAKK
   git remote rename origin upstream
   git remote add origin <OUR REPO URL>
   git branch -M main
   ```
   If `pokerMAKK` already has commits, instead pull the starter files into it
   (`git remote add upstream ...; git fetch upstream; git merge upstream/main --allow-unrelated-histories`)
   and keep the starter files unchanged.
2. In `agent.py`, set `PARTICIPANT = "pokerMAKK"` and `AGENT_NAME = "MAKK"`.
3. Create a venv, install `requirements.txt` and `requirements-dev.txt`, run `python -m pytest -q`.
4. Save this file as `PLAN_CODEX.md` in the repo root. Create `AGENTS.md` (section 2).
5. Commit "Starter + plan" and push to `origin main`.

---

## 2. AGENTS.md (create exactly this at the repo root)

```md
# Rules for coding agents in pokerMAKK

- Never edit the SERVER PLUMBING section of agent.py, or game.py, evaluator.py, judge_engine.py,
  docker/, tools/, baseline-bots/.
- agent.py's YOUR CODE HERE section only forwards to bots/active.py. Bot logic lives in bots/.
- Every bot module exposes new_half(config, memory), choose_action(obs, memory) -> Action,
  on_hand_end(result, memory), and is called only through bots/common/safe.py.
- Keep per-half state in `memory`, never in module globals. Write files only under /tmp.
- Every returned action must be in obs.legal_actions.
- Decision time: about 2 ms on average, under 4 s total per half. Check with
  `python league/run.py --timing`.
- Score hands only with evaluator.omaha_score.
- Before calling a task done: `python -m pytest -q` and
  `python league/run.py --bot <name> --zoo all --seeds 3` must pass with 0 errors.
- Append every league run to league/results.csv. Never delete rows.
- Files under 100 MB, no Git LFS.
```

---

## 3. Target layout

```
agent.py                  # starter; YOUR CODE HERE forwards to bots.active
requirements.txt          # starter pins (+ numpy only if a bot needs it)
game.py evaluator.py judge_engine.py baseline-bots/ tools/ docker/ test_agent.py   # unchanged
AGENTS.md
PLAN_CODEX.md
bots/
  __init__.py
  active.py               # ACTIVE_BOT = "m1_equity"
  common/
    __init__.py
    safe.py               # safety wrapper
    cards.py              # canonicalization, features, draw detection
    equity.py             # Monte Carlo equity with time cap + cache
    timing.py             # per-half time accounting
  m1_equity/   __init__.py bot.py tables/      # Person A
  m2_cfr/      __init__.py bot.py train/ tables/   # Person B
  m3_exploit/  __init__.py bot.py stats.py archetypes.py   # Person C
  m4_learned/  __init__.py bot.py train/ weights/   # Person D
league/
  run.py                  # in-process duplicate league
  zoo/                    # opponent bots (same three-function interface)
  results.csv
tests/
  test_safe.py test_legal_fuzz.py test_league.py
data/                     # small shared tables
```

---

## 4. Phase 1: shared infrastructure (do this first; everyone depends on it)

### 4.1 `bots/common/safe.py`
`wrap(module)` returns an object with the three functions:
- `choose_action`: call the bot in try/except. If it raises, returns something not in
  `obs.legal_actions`, or the half's thinking time has passed 6 s, return CHECK_CALL if legal and
  `to_call == 0`, otherwise CHECK_CALL if the call is cheap (to_call <= 2) else FOLD. Count fallbacks in
  `memory["_fallbacks"]`.
- `on_hand_end` and `new_half`: try/except, swallow errors, never raise.
- Measure time per decision with `time.perf_counter()` and keep the running total in `memory["_think_s"]`.

### 4.2 `agent.py` YOUR CODE HERE section
Replace the three example functions with thin forwarders:
```python
from bots.active import get_bot
_BOT = get_bot()          # wrapped by safe.py; import + table loading happens here at startup

def new_half(config, memory): _BOT.new_half(config, memory)
def choose_action(obs, memory): return _BOT.choose_action(obs, memory)
def on_hand_end(result, memory): _BOT.on_hand_end(result, memory)
```
`get_bot()` reads `ACTIVE_BOT`, imports `bots.<name>.bot`, calls its optional `load()` and returns `safe.wrap(...)`.

### 4.3 `league/run.py` (in-process duplicate league)
- Uses `game.make_deal(seed, i)`, `game.button_for_deal(i)`, `game.Game(deal, button_seat, hand_index)`,
  `game.observation(seat)`, `game.legal_actions()`, `game.apply(action)`, `game.hand_result(seat)`.
  Read `game.py` and `judge_engine.py` to mirror the judge exactly (half 1 and half 2 seat swap, how
  results are delivered, default action on errors/timeouts).
- Each half: fresh `memory` dicts, `new_half` for both bots, play deals 0..N-1, call `on_hand_end` for
  both after each hand.
- Output per match: our bb/deal, 95% interval (per-deal duplicate sums), verdict (win/chop/loss), errors,
  fallbacks, p50/p99 decision ms, total thinking s per half.
- CLI: `--bot NAME`, `--opp NAME|all`, `--deals 1000`, `--seeds 3`, `--timing`, `--out league/results.csv`.
  Bot names resolve to `bots.<name>.bot` or `league.zoo.<name>`.
- **Validation:** for one seed, our league and `judge_engine.py` (HTTP) must give the same chip result
  for the same two bots. Add this as `tests/test_league.py`.

### 4.4 `league/zoo/`
Each opponent uses the same three-function interface:
- `random`, `calling_station`, `always_half`, `always_pot` (ported from `baseline-bots/`)
- `nit`: plays only top ~20% hands preflop, folds to aggression without a strong made hand
- `loose_passive`: calls with any equity > 25%, rarely raises
- `maniac`: RAISE_POT whenever legal, else call
- `shover`: preflop RAISE_POT to all-in with top 40%, else fold
- `fold_to_raise`: plays normally but folds to any raise unless very strong
- later: snapshots of our own bots (`m1_v1`, `m3_v1`, ...)

### 4.5 Tests
- `test_safe.py`: a bot that raises, returns illegal actions, or sleeps is caught; no exception escapes.
- `test_legal_fuzz.py`: 5,000 random game states for each bot; action always legal.
- Run `python -m pytest -q`, `./tools/check_build.sh`. Commit "Phase 1: infra", push.

---

## 5. Phase 2: Method 1 (Person A) `bots/m1_equity`

Equity-threshold bot based on Billings et al. (effective hand strength).

1. `bots/common/equity.py`: Monte Carlo equity vs a random hand (or a weighted range) using
   `omaha_score`. Deal opponent 5 cards + remaining board from the unseen deck. Hard cap per call
   (default 1.5 ms or 60 samples). Cache by (canonical hole, board).
2. Preflop table: `bots/m1_equity/tables/preflop.npy` (or a JSON dict) of equity vs random for
   suit-canonical 5-card hands (map suits to a canonical order). Build with
   `bots/m1_equity/build_preflop.py` using many samples; load at startup. Keep the file small.
3. Decision rule per street:
   - Pot odds = to_call / (pot + to_call).
   - Postflop strength = EHS = HS + (1 - HS) * Ppot approximation via equity.
   - Raise thresholds: `value_pot`, `value_half`, call if equity > pot odds + `margin`, else check/fold.
   - Small bluff frequency on the river when checked to, `bluff_freq`.
   - Position adjustment for button.
4. Parameters in `bots/m1_equity/params.json`. Grid search in the league:
   `value_pot in {0.70,0.75,0.80}`, `value_half in {0.55,0.60,0.65}`, `margin in {0,0.03,0.06}`,
   `bluff_freq in {0,0.05,0.10}`.
5. **A1 milestone:** v0 bot with defaults, 0 errors, beats all four baselines over 3 seeds through the
   real `judge_engine.py`. Set `ACTIVE_BOT = "m1_equity"`, commit, push. This is our first submission.

---

## 6. Phase 3: Method 3 (Person C) `bots/m3_exploit`

Opponent modeling wrapped around a base bot (default m1_equity). Based on Billings 1998 (re-weighting),
Johanson 2007 (robust counter-strategies), Ganzfried & Sandholm 2011 (DBBR).

1. `stats.py`: per-half opponent stats in `memory` with Beta priors: VPIP, preflop raise rate,
   aggression per street, fold-to-RAISE_HALF and fold-to-RAISE_POT per street, showdown rate,
   shown-hand equity by line (from `result.opp_hole`). Updated in `on_hand_end` and from
   `obs.action_history`.
2. `archetypes.py`: classify station / nit / maniac / random / solid after 50, 100, 200 hands.
   Target: >90% correct on zoo bots by hand 200.
3. Exploits:
   - station: no bluffs, value-bet thinner (lower raise thresholds)
   - nit: steal preflop, bluff more when checked to
   - maniac: call down wider, trap with strong hands
   - over-folder: RAISE_POT more often
4. Range-weighted equity: weight opponent hands by their actions (stronger range after raises).
5. Safety: exploit weight grows with number of observations; if our running result in the half drops
   below -1 standard error, revert to the base bot.
6. Measure per-deal standard deviation in duplicate per archetype; log it, so we know the edge needed to win.

Keep a change only if it passes the adoption rule (section 10).

---

## 7. Phase 4: Method 2 (Person B) `bots/m2_cfr`

Approximate equilibrium via MCCFR (Zinkevich 2007, Lanctot 2009, CFR+ from Bowling 2015,
abstraction from Ganzfried & Sandholm 2014).

1. Betting abstraction: the real game's tree (4 actions, max 4 raises/street, 80-chip stacks) is used
   exactly. Card abstraction only.
2. Card buckets (imperfect recall): preflop K=20 by equity; flop/turn/river 50 each by
   (equity, equity squared / potential) with k-means. Store bucket boundaries/centers in `tables/`.
3. Train in `train/mccfr.py`: external-sampling MCCFR with regret matching+ and linear averaging over a
   pool of 1-2M pre-generated deals; numpy (numba if installed). Save the average strategy as a
   compact table (float16) under 100 MB. Train offline, overnight if needed.
4. Runtime `bot.py`: compute bucket (equity via `bots/common/equity.py` or Method 4's model), look up
   the strategy by (street, betting history, bucket), sample an action, map to legal.
5. Checks: exploitability proxy (best-response bot from Method 1 grid against it), league results,
   startup time with the table loaded.

---

## 8. Phase 5: Method 4 (Person D) `bots/m4_learned`

1. Data: `train/gen_data.py` makes 1-2M (hole, board) states per street labeled with Monte Carlo equity
   vs a random hand at 2,000 samples.
2. Model: `train/train.py`, features = suit-canonical rank counts, suit structure, made-hand category,
   flush/straight draw flags, board texture. Gradient boosting or an MLP (2 hidden layers, 64-256 units).
   Export weights to `weights/` as `.npz`; inference in pure numpy.
   Target: MAE < 0.02 held out, < 0.1 ms per call.
3. `bots/common/equity.py` gets `fast_equity()` that uses the model when weights exist, else Monte Carlo.
4. Range-conditioned version: add opponent aggression level as an input (labels vs action-filtered ranges).
5. PSRO-lite (Lanctot 2017): `league/psro.py` builds the payoff matrix between all our bots and the zoo,
   solves for the mixture, tunes a Method 1/3 variant as best response, adds it; 3-5 rounds.
6. Stretch only: NFSP or a small policy net (Heinrich & Silver 2016).

---

## 9. Final assembly

- `bots/active.py` picks the final bot (expected: m1 or m2 as base, m3 exploitation on top, m4 equity inside).
- If combining, create `bots/final/bot.py` that composes them; it still goes through `safe.py`.

---

## 10. Adoption rule (a change replaces the current bot only if all hold)

1. Zero errors and zero illegal actions in all league runs.
2. p99 decision time under 20 ms and total thinking under 4 s per half.
3. No zoo opponent moves from win to chop, or chop to loss.
4. Expected points (win 1, chop 0.5, loss 0) go up, or are equal and the paired bb/deal gain over at least
   5 seeds x 1,000 deals has a 95% interval above 0. Both candidates use the same seeds.

---

## 11. Before every submission

- [ ] `python -m pytest -q`, `./tools/check_build.sh` and `tools/smoke_test.py` pass.
- [ ] Startup under 15 s on 1 CPU (time `python -c "import agent"`).
- [ ] Real HTTP matches with `judge_engine.py` vs all four baselines, 3 seeds: 0 errors, all wins.
- [ ] No file over 100 MB, no Git LFS, nothing written outside `/tmp`.
- [ ] `bots/active.py` names the intended bot.
- [ ] Repo is **public**. Push, copy the full 40-character commit SHA (`git rev-parse HEAD`), submit the form,
      confirm the build succeeded.

---

## 12. How teammates use this

Each person opens pokerMAKK in Codex or Claude Code after Phase 1 is pushed and says:

> Read AGENTS.md and PLAN_CODEX.md. Do the phase for my method: <Method N, folder bots/mN_...>.
> Only edit files in that folder unless the plan says otherwise. Run the league on the full zoo with
> 3 seeds, append to league/results.csv, run pytest, then commit and push to a branch named <name>-mN.

Merge to main only through the adoption rule.


---

## Implementation status (2026-11-07)

- Starter `heads-up-bundle` merged from `upstream/main`; the original starter runtime files are preserved except for the required participant identity and the marked bot forwarding section in `agent.py`.
- Phase 1 infrastructure is present: `bots/common/{safe,cards,equity,timing}.py`, `league/run.py`, zoo opponents, and the safety, fuzz, and league tests.
- Method 1 is active. Its suit-canonical preflop table has 19,998 entries, generated with 100 samples per hand. The equity estimator uses deterministic, cached Monte Carlo evaluations through `evaluator.omaha_score`.
- Method 2 has a trained 150-state, coarse regret-matching table. Its trainer solves abstract one-street payoff states as a warm start; it is not a full-game MCCFR solution yet.
- Method 3 has per-half opponent statistics, archetype rules, conservative exploits, and a base-strategy reversion guard. It remains experimental.
- Method 4 has feature generation and NumPy training code. A 20,000-state experiment produced held-out MAE above 0.14, so the runtime rejects the model and falls back to Method 1 until a model meets the 0.05 MAE gate.
- `league/psro.py` reads payoff results and calculates a simple population mixture. It needs complete payoff data for each candidate before its mixture is meaningful.

### Checks completed

- `python3 -m pytest -q`: 16 passed.
- `python3 tools/smoke_test.py --port 5008`: passed; all five sample decisions were legal and returned in 1–4 ms.
- Startup: about 0.4 seconds on the development machine.
- Real HTTP duplicate matches: Method 1 won all three 1,000-deal seeds against each starter baseline, with zero errors.
- In-process league: Method 1 won all three 1,000-deal seeds against each of the nine zoo opponents, with zero errors and fallbacks. Targeted timing runs measured each half at 2.19–2.38 seconds worst-case and p99 decisions below 1.2 ms.
- Methods 2–4 passed 5,000-state legal-action fuzzing and short all-zoo league smoke runs with zero errors. These short runs are not adoption evidence.
- `./tools/check_build.sh` could not complete: Docker Desktop first failed while extracting the PyTorch base image with a disk I/O error, then stopped answering `docker info`. Direct server smoke tests passed. Retry the Docker check after Docker Desktop is healthy.

The first HTTP baseline batch left nine mislabeled rows in `league/results.csv`; `league/results_notes.md` identifies those append-only rows and the corrected rerun.
