import torch

from src.utils.metrics import summarize


def test_summary_reports_feasibility_and_cost():
    result = summarize(
        cost=torch.tensor([3.0, 5.0]),
        feasible=torch.tensor([True, False]),
        distance=torch.tensor([3.0, 4.0]),
        vehicles_used=torch.tensor([1, 2]),
    )

    assert result["mean_cost"] == 4.0
    assert result["feasibility_rate"] == 0.5
    assert result["mean_feasible_cost"] == 3.0
