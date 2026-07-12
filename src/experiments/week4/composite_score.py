#!/usr/bin/env python3
"""Week 4 tested method: composite-score greedy customer selection.

Week 3 showed that a due-time-only priority (Method A) loses to the
nearest-customer baseline (Method B): it triggers coverage failures and
produces spatially inefficient routes.  Week 3's recommended next step was a
scoring rule that combines travel distance, due-time urgency, remaining
battery headroom, and depot-return reserve instead of ranking on a single
feature.

Method C implements that composite score.  It still consumes exactly the same
feasible-candidate list produced by the shared week 3/4 feasibility checker, so
the comparison against Methods A and B stays controlled: only the ranking rule
changes.
"""

from __future__ import annotations

METHOD_ID = "C_composite_score"
METHOD_ROLE = "tested_method"
DESCRIPTION = (
    "Greedy selection that ranks feasible customers by a weighted score of "
    "normalized travel distance, due-time urgency, and time-window slack."
)

# Weights are fixed before the experiment and shared across all instance
# scales so the method is not tuned per instance.  Distance dominates to keep
# routes compact (the Week 3 failure mode), while urgency and slack break ties
# toward customers that would otherwise become infeasible later.
WEIGHT_DISTANCE = 1.0
WEIGHT_URGENCY = 0.35
WEIGHT_SLACK = 0.25


def select_customer(candidates: list[tuple[float, float, float, float, int]]) -> int:
    """Return the customer id with the smallest composite score.

    Each candidate is
    ``(norm_distance, norm_urgency, norm_slack, raw_distance, customer_id)``
    where the three normalized terms lie in ``[0, 1]``.  A lower score is
    better: near customers, urgent due times, and tight remaining slack are all
    preferred.  ``raw_distance`` and ``customer_id`` are deterministic
    tie-breakers so the ranking is reproducible.
    """
    def score(candidate: tuple[float, float, float, float, int]) -> tuple[float, float, int]:
        norm_distance, norm_urgency, norm_slack, raw_distance, customer_id = candidate
        composite = (
            WEIGHT_DISTANCE * norm_distance
            + WEIGHT_URGENCY * norm_urgency
            + WEIGHT_SLACK * norm_slack
        )
        return (composite, raw_distance, customer_id)

    return min(candidates, key=score)[4]
