# Deep RL for Electric Vehicle Routing with Time Windows (EVRP-TW)

> **Faculty Undergraduate Research Practice (FURP)**
> Undergraduate Research Group · Faculty of Science and Engineering · University of Nottingham Ningbo China

This repository contains the FURP research project on attention-based deep
reinforcement learning for the Electric Vehicle Routing Problem with Time
Windows (EVRP-TW).

---

## Project Info

| Field | Entry |
|---|---|
| Student name(s) | _Chenyu Fan_ |
| Project title | _Deep RL for Electric Vehicle Routing with Time Windows (EVRP-TW)_ |
| Project tag | _EVRP-TW-DeepRL_ |
| Track | Research |
| Supervising faculty | _Tianxiang Cui_ |
| Project lead | _Tianxiang Cui_ |
| Team or individual | _Individual_ |
| Cited papers / reading notes | See `docs/reading_notes/` (examples: `01_Attention_Model_Kool2018.md`, `02_DRL_EVRPTW_Lin2021.md`, `03_POMO_Kwon2020.md`, `04_EVRPTW_Schneider2014.md`) |

**One-line summary:** This project implements reproducible baselines and
evaluation protocols for vehicle-routing and electric-vehicle-routing problems
with capacity, time-window, battery, charging, and fleet constraints, and
explores attention-based deep-RL approaches and feasibility-aware heuristics.

---

## Research Scope

The repository contains reproducible experiments, baseline methods, and result
artifacts developed over the weekly cadence of the FURP project. Current
implemented and committed components include:

- Week 1: OR-Tools baselines and runnable examples for TSP, VRP, CVRP, and VRPTW (see `src/experiments/week1/`).
- Week 2: EVRP-TW baseline comparison scripts and result exporters (see `src/experiments/week2/`).
- Week 3: Controlled greedy-policy comparison and a feasibility-first greedy baseline reproduction (see `src/experiments/week3/`).
- Week 4: Composite-score greedy method `C_composite_score` with feasibility-aware 2-opt local search and controlled experiments comparing methods A/B/C (see `src/experiments/week4/`).
- Week 5: Local two-run reproducibility check for the fixed Week 4 configuration, with deterministic aggregate comparison (see [`docs/week5_project_checkpoint.md`](docs/week5_project_checkpoint.md)).
- Result tables, route visualisations, run logs, and diagnostic reports under `src/experiments/*/results/` and `src/results/`.

Main evaluation metrics used in experiments: feasibility rate, feasible route cost (objective), route distance, vehicles used, runtime, time-window violations, battery/charging violations, and coverage violations. Experiments currently assume homogeneous vehicles, deterministic Euclidean travel distances, linear energy consumption, and full recharging at stations unless noted in the experiment README.

---

## Research Visualizations

Selected research figures and supporting regeneration instructions are stored in `src/results` and per-week `results/` folders:

- `src/results/LOCAL_RUNS.md` — commands used to regenerate committed results locally.
- Week-specific figure files can be found in `src/experiments/week*/results/` (e.g. week3 & week4 figures).

The committed visualisations can be regenerated with the per-week commands (examples below) or with the top-level results script:

```bash
# Top-level results generator (if present)
python3 src/results/generate_research_visualizations.py

# Or run per-week experiment runners:
python3 src/experiments/week1/compare_or_tools_baselines.py
python3 src/experiments/week2/compare_week2_baselines.py --scales 50 100 200 --seed 20260621 --or-time-limit 8
python3 src/experiments/week3/compare_week3_baselines.py --scales 20 50 100 --instances-per-scale 12 --seed 20260630
python3 src/experiments/week4/compare_week4_methods.py

# Week 5 local reproducibility check (runs the fixed Week 4 comparison twice)
python3 src/experiments/week5/run_reproducibility_check.py
```

The Week 5 check compares deterministic aggregate fields only; runtime is
recorded but excluded because it can vary with local system load. Its generated
summary is [`src/experiments/week5/results/week5_reproducibility.md`](src/experiments/week5/results/week5_reproducibility.md).

---

## Repository structure

This structure is **mandatory** — please keep it intact.

```
/docs
 ├── 00_weekly.md         ← update EVERY week: progress, challenges, next steps
 └── meeting_notes/       ← key takeaways from all team meetings
/src
 ├── data/                 dataset notes or placeholders
 ├── experiments/
 │   ├── week1/            ← OR-Tools routing baselines
 │   ├── week2/            ← EVRP-TW baseline comparison
 │   ├── week3/            ← controlled greedy-policy comparison
 │   ├── week4/            ← composite-score method and further experiments
 │   └── week5/            ← local reproducibility verification
 └── results/              ← selected figures and compact results
FURP_Showcase.pdf         ← your poster / presentation PDF, in the repo root
```

- **`docs/00_weekly.md`** — your weekly progress log. This is the first thing we check.
- **`docs/meeting_notes/`** — one file per meeting with key takeaways and action items.
- **`src/experiments/`** — week-by-week reproducible experiments and results.
- **`src/results/`** — selected figures and compact research outputs.
- **`FURP_Showcase.pdf`** — your final poster, placed in the **repo root** with this exact filename.

---

## The three rules for your certificate

To earn your FURP certificate, **all three** must be satisfied:

1. **Attend > 50%** of programme activities (weekly meetings, workshops, scheduled sessions — online or in person).
2. **Submit a poster** — place it as `FURP_Showcase.pdf` in this repo root.
3. **Present at the Poster Showcase** — in person (strongly preferred), or send a stand-in if you truly cannot attend.

> Miss any one of the three, and the certificate is not awarded this round.

**Research Track — minimum for certification:** successful replication of a cited paper with at least **10% innovation** (reproduce the work *and* add something new).

---

## Weekly cadence

Every week, you should:

- ✅ Update [`docs/00_weekly.md`](docs/00_weekly.md)
- ✅ Log meeting notes in [`docs/meeting_notes/`](docs/meeting_notes/)
- ✅ Attend the weekly meeting (online or in person)

Consistent weekly engagement is the backbone of a successful FURP project — and it feeds directly into your attendance (Rule 1).

---

## Leave & withdrawal

Any **leave of absence** or **withdrawal** must be notified to us **by email** — a verbal or chat message is not sufficient.

- **Leave:** email *before* the session where possible, state the date(s) and reason. Note that leave still counts against the >50% attendance rule.
- **Withdrawal:** email us to formally withdraw so we can free your project slot and update records.
- **Switching tracks:** email the project lead with the subject *"Project Transfer Request"* and CC your supervising faculty member.

> No email = no record. Always put leave and withdrawal in writing.

---

## Project checklist

- [x] Created and published the project repository
- [x] Added Week 1 OR-Tools routing baselines
- [x] Added Week 2 EVRP-TW baseline comparison artifacts
- [x] Added Week 3 baseline reproduction with runtime and feasibility logs
- [x] Added Week 4 composite-score method and controlled experiments
- [x] Added Week 5 local reproducibility checkpoint and evidence
- [x] Started `docs/00_weekly.md`
- [x] Created my first file in `docs/meeting_notes/`
- [ ] Confirm the final cited paper and formal experimental protocol (see `docs/reading_notes/`)
- [ ] Add `FURP_Showcase.pdf` to the repo root before the Showcase

---

*Bridging the gap between classroom knowledge and cutting-edge research.*
