"""Model utilities for profile detection."""

from __future__ import annotations

from pathlib import Path
from typing import List, Sequence, Tuple

import joblib
from sklearn.ensemble import RandomForestClassifier

from neurobridge.core.profile import Profile

MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"

PROFILE_ORDER = [
    Profile.ADHD.value,
    Profile.AUTISM.value,
    Profile.DYSLEXIA.value,
    Profile.ANXIETY.value,
    Profile.DYSCALCULIA.value,
]


def build_model(random_state: int = 42) -> RandomForestClassifier:
    """Create a lightweight random forest classifier."""

    return RandomForestClassifier(
        n_estimators=80,
        max_depth=8,
        min_samples_leaf=2,
        random_state=random_state,
        n_jobs=1,
    )


def save_model(model: RandomForestClassifier, path: Path = MODEL_PATH) -> None:
    """Persist a trained model to package path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)


def load_model(path: Path = MODEL_PATH) -> RandomForestClassifier:
    """Load trained model from package path."""

    return joblib.load(path)


def predict_with_confidence(
    model: RandomForestClassifier,
    features: Sequence[float],
) -> Tuple[str, float, List[Tuple[str, float]]]:
    """Predict profile label with confidence and ranking details."""

    probs = model.predict_proba([list(features)])[0]
    classes = [str(label) for label in model.classes_]
    ranked = sorted(zip(classes, probs), key=lambda item: item[1], reverse=True)
    top_label, top_prob = ranked[0]
    return top_label, float(top_prob), [(label, float(prob)) for label, prob in ranked]
