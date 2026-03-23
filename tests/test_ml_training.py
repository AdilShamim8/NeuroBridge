"""Tests for synthetic data generation and model training utilities."""

from pathlib import Path

from neurobridge.core.profile import Profile
from neurobridge.ml.data.generator import generate_synthetic_samples, to_training_matrices
from neurobridge.ml.trainer import TrainingReport, main, train_model


def test_generate_synthetic_samples_shape_and_labels() -> None:
    samples = generate_synthetic_samples(per_profile=4, seed=7)

    assert len(samples) == 20
    assert len(samples[0].features) == 15
    labels = {sample.label for sample in samples}
    expected_labels = {
        Profile.ADHD.value,
        Profile.AUTISM.value,
        Profile.DYSLEXIA.value,
        Profile.ANXIETY.value,
        Profile.DYSCALCULIA.value,
    }
    assert labels == expected_labels


def test_generate_synthetic_samples_deterministic_with_seed() -> None:
    first = generate_synthetic_samples(per_profile=2, seed=9)
    second = generate_synthetic_samples(per_profile=2, seed=9)

    assert first == second


def test_to_training_matrices_preserves_order() -> None:
    samples = generate_synthetic_samples(per_profile=2, seed=4)
    x_all, y_all = to_training_matrices(samples)

    assert len(x_all) == len(samples)
    assert len(y_all) == len(samples)
    assert x_all[0] == samples[0].features
    assert y_all[0] == samples[0].label


def test_train_model_creates_artifact_and_report(tmp_path: Path) -> None:
    output_model = tmp_path / "detector.pkl"

    result = train_model(
        per_profile=12,
        test_size=0.25,
        random_state=11,
        model_path=output_model,
    )

    assert isinstance(result, TrainingReport)
    assert 0.0 <= result.accuracy <= 1.0
    assert "precision" in result.classification_report
    assert result.model_path == str(output_model)
    assert output_model.exists()


def test_main_prints_summary(monkeypatch, capsys) -> None:
    fake_report = TrainingReport(
        accuracy=0.95,
        classification_report="classification report",
        confusion_matrix="[[1, 0], [0, 1]]",
        model_path="model.pkl",
    )

    monkeypatch.setattr("neurobridge.ml.trainer.train_model", lambda: fake_report)
    main()

    output = capsys.readouterr().out
    assert "Profile detector training completed" in output
    assert "accuracy: 0.9500" in output
    assert "classification report" in output
    assert "model saved to: model.pkl" in output
