"""Week 3 due-time-priority greedy customer selector."""

from __future__ import annotations

METHOD_ID = "A_due_time_priority"
METHOD_ROLE = "tested_method"
DESCRIPTION = "Choose the feasible customer with earliest due-time priority."


def select_customer(candidates: list[tuple[float, float, int]]) -> int:
    """Select by earliest due time, breaking ties by travel distance."""
    # Candidate tuple layout: (travel_distance_from_current, due_time, id).
    # This method prioritizes time-window urgency before route compactness.
    return min((due, leg, customer_id) for leg, due, customer_id in candidates)[2]
