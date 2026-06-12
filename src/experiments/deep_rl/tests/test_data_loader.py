import torch

from src.utils.data_loader import DataConfig, generate_batch, load_dataset, save_dataset


def test_generation_is_deterministic_and_has_expected_shapes():
    config = DataConfig(num_customers=5, num_stations=2)
    first = generate_batch(3, config, seed=7)
    second = generate_batch(3, config, seed=7)

    assert first["coords"].shape == (3, 8, 2)
    assert first["demand"].shape == (3, 8)
    assert torch.equal(first["coords"], second["coords"])
    assert torch.all(first["node_type"][:, 0] == 0)
    assert torch.all(first["node_type"][:, -2:] == 2)


def test_dataset_round_trip(tmp_path):
    config = DataConfig(num_customers=3, num_stations=1)
    batch = generate_batch(2, config, seed=9)
    path = tmp_path / "dataset.npz"

    save_dataset(path, [batch], config)
    restored = load_dataset(path)

    assert torch.equal(batch["coords"], restored["coords"])
    assert torch.equal(batch["node_type"], restored["node_type"])
