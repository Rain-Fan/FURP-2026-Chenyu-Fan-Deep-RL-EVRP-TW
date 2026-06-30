# Deep RL for Electric Vehicle Routing with Time Windows (EVRP-TW)

> **Faculty Undergraduate Research Practice (FURP)**
> Undergraduate Research Group · Faculty of Science and Engineering · University of Nottingham Ningbo China

This repository contains the FURP research project on attention-based deep
reinforcement learning for the Electric Vehicle Routing Problem with Time
Windows (EVRP-TW).

---

## Project Info

| Field | Your entry |
|---|---|
| Student name(s) | _Chenyu Fan_ |
| Project title | _Deep RL for Electric Vehicle Routing with Time Windows (EVRP-TW)_ |
| Project tag | _EVRP-TW-DeepRL_ |
| Track | Research |
| Supervising faculty | _Tianxiang Cui_ |
| Project lead | _Tianxiang Cui_ |
| Team or individual | _Individual_ |
| Cited paper being replicated | _To be confirmed: add title and link/DOI_ |

**One-line summary:** This project studies reproducible baselines and
evaluation protocols for vehicle-routing and electric-vehicle-routing problems
with capacity, time-window, battery, charging, and fleet constraints.

---

## Research Scope

The current implementation includes:

- Week 1 OR-Tools baselines for TSP, VRP, CVRP, and VRPTW;
- Week 2 EVRP-TW baseline comparison artifacts;
- Week 3 feasibility-first greedy EVRP-TW baseline reproduction;
- result tables, route visualisations, run logs, and diagnostic reports.

The main evaluation metrics are feasibility rate, route cost, distance,
vehicles used, runtime, time-window violations, battery or charging
violations, and coverage violations. The current experiments assume
homogeneous vehicles, deterministic Euclidean travel, linear energy use, and
full charging at stations.

---

## Repository structure

This structure is **mandatory** — please keep it intact.

```
/docs
 ├── 00_weekly.md         ← update EVERY week: progress, challenges, next steps
 └── meeting_notes/       ← key takeaways from all team meetings
/src
 ├── experiments/week1_or_tools_baselines/
 ├── experiments/week2_baselines/
 ├── experiments/week3_baseline/
 └── results/             ← selected figures and compact results
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
- [x] Started `docs/00_weekly.md`
- [x] Created my first file in `docs/meeting_notes/`
- [ ] Confirmed the cited paper and final experimental protocol
- [ ] (By Showcase) Added `FURP_Showcase.pdf` to the repo root

---

*Bridging the gap between classroom knowledge and cutting-edge research.*
