"""Week 3 nearest-customer greedy baseline selector."""

from __future__ import annotations

METHOD_ID = "B_nearest_customer"
METHOD_ROLE = "baseline"
DESCRIPTION = "Choose the feasible customer with shortest current travel distance."


def select_customer(candidates: list[tuple[float, float, int]]) -> int:
    """Select by shortest current travel distance, breaking ties by due time."""
    # Candidate tuple layout: (travel_distance_from_current, due_time, id).
    # This baseline prioritizes compact routes before time-window urgency.
    return min((leg, due, customer_id) for leg, due, customer_id in candidates)[2]
