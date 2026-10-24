"""Model utilities for profile detection.

Security note: joblib.load() (like pickle) can execute arbitrary code.
Only load model artifacts that you built yourself from this repository's
trainer; never load a ``.pkl`` file from an untrusted source.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import joblib
import sklearn
from sklearn.ensemble import RandomForestClassifier

from neurobridge.core.profile import Profile

MODEL_PATH = Path(__file__).resolve().parent / "model.pkl"


class ModelCompatibilityError(RuntimeError):
    """Raised when the runtime scikit-learn cannot safely unpickle the artifact."""


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


def save_model(model: RandomForestClassifier, path: Path = MODEL_PATH) -> Path:
    """Persist a trained model plus training metadata.

    The metadata records the scikit-learn version and feature count used at
    training time so ``load_model`` can refuse cross-version unpickling
    instead of silently predicting with an incompatible estimator.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, path)
    meta_path = path.with_name(path.name + ".meta.json")
    meta = {
        "sklearn_version": sklearn.__version__,
        "feature_count": int(getattr(model, "n_features_in_", 0)),
        "profile_order": PROFILE_ORDER,
        "model_class": type(model).__name__,
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta_path


def _training_version(meta_path: Path) -> str | None:
    """Return the scikit-learn version recorded next to the artifact."""

    if not meta_path.exists():
        return None
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    version = meta.get("sklearn_version")
    return str(version) if version else None


def load_model(path: Path = MODEL_PATH) -> RandomForestClassifier:
    """Load trained model from package path.

    Raises ModelCompatibilityError when the artifact was trained with a
    different scikit-learn minor version: sklearn cannot guarantee that an
    estimator unpickled across versions produces valid predictions, so the
    detector falls back to the quiz flow instead of guessing.
    """

    trained_with = _training_version(path.with_name(path.name + ".meta.json"))
    runtime = sklearn.__version__
    if trained_with is not None and trained_with.split(".")[:2] != runtime.split(".")[:2]:
        raise ModelCompatibilityError(
            f"Model artifact {path.name} was trained with scikit-learn "
            f"{trained_with} but the runtime is {runtime}; "
            "refusing to unpickle across minor versions. Retrain with "
            "python -m neurobridge.ml.trainer to regenerate the artifact."
        )
    return joblib.load(path)  # type: ignore[no-any-return]


def predict_with_confidence(
    model: RandomForestClassifier,
    features: Sequence[float],
) -> tuple[str, float, list[tuple[str, float]]]:
    """Predict profile label with confidence and ranking details."""

    probs = model.predict_proba([list(features)])[0]
    classes = [str(label) for label in model.classes_]
    ranked = sorted(zip(classes, probs), key=lambda item: item[1], reverse=True)
    top_label, top_prob = ranked[0]
    return top_label, float(top_prob), [(label, float(prob)) for label, prob in ranked]
