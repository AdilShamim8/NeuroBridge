"""Training script for ML profile detection model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from neurobridge.ml.data.generator import generate_synthetic_samples, to_training_matrices
from neurobridge.ml.model import MODEL_PATH, build_model, save_model


@dataclass(frozen=True)
class TrainingReport:
    """Structured report for model training run."""

    accuracy: float
    classification_report: str
    confusion_matrix: str
    model_path: str


def train_model(
    per_profile: int = 1000,
    test_size: float = 0.2,
    random_state: int = 42,
    model_path: Path = MODEL_PATH,
) -> TrainingReport:
    """Train RandomForest classifier on synthetic profile interaction data."""

    samples = generate_synthetic_samples(per_profile=per_profile, seed=random_state)
    x_all, y_all = to_training_matrices(samples)

    x_train, x_test, y_train, y_test = train_test_split(
        x_all,
        y_all,
        test_size=test_size,
        random_state=random_state,
        stratify=y_all,
    )

    model = build_model(random_state=random_state)
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    accuracy = float(accuracy_score(y_test, y_pred))
    report = classification_report(y_test, y_pred)
    matrix = confusion_matrix(y_test, y_pred)

    save_model(model, path=model_path)

    return TrainingReport(
        accuracy=accuracy,
        classification_report=report,
        confusion_matrix=str(matrix),
        model_path=str(model_path),
    )


def main() -> None:
    """Train model and print a concise report."""

    result = train_model()
    print("Profile detector training completed")
    print(f"accuracy: {result.accuracy:.4f}")
    print("classification report:")
    print(result.classification_report)
    print("confusion matrix:")
    print(result.confusion_matrix)
    print(f"model saved to: {result.model_path}")


if __name__ == "__main__":
    main()
