"""Tests for profile detector behavior."""

import json

import pytest

from neurobridge.ml.detector import ProfileDetector
from neurobridge.ml.model import ModelCompatibilityError, load_model
from neurobridge.ml.trainer import train_model


def test_detector_falls_back_with_no_events() -> None:
    detector = ProfileDetector()
    result = detector.detect([])
    assert result.fallback_to_quiz is True
    assert result.confidence == 0.0
    from neurobridge.core.profile import Profile

    assert result.profile == Profile.ADHD


def test_detector_returns_reasoning_for_minimal_events() -> None:
    detector = ProfileDetector()
    events = [
        {"event_type": "chunk_dwell", "metadata": {"dwell_ms": 650, "scroll_speed": 2.8}},
        {"event_type": "chunk_reread", "metadata": {"chunk_index": 0, "is_calming": False}},
        {"event_type": "section_skipped", "metadata": {"contains_urgency": True}},
        {"event_type": "text_edited", "metadata": {"edit_ratio": 0.22}},
    ]
    result = detector.detect(events)
    assert isinstance(result.profile, str)
    # The reasoning must name which path executed; the OR-assert previously
    # passed whichever branch fired (or neither, since the string check had no
    # else-clause), so add the no-events contract explicitly.
    assert result.reasoning.strip()
    assert "Top probabilities" in result.reasoning or "Falling back to quiz" in result.reasoning


def test_detector_falls_back_when_model_is_unavailable(monkeypatch) -> None:
    monkeypatch.setattr(
        "neurobridge.ml.detector.load_model", lambda: (_ for _ in ()).throw(RuntimeError("missing"))
    )
    detector = ProfileDetector()

    events = [{"event_type": "chunk_dwell", "metadata": {"dwell_ms": 400, "scroll_speed": 1.3}}]
    result = detector.detect(events)

    assert result.fallback_to_quiz is True
    assert result.confidence == 0.0
    assert "Model unavailable" in result.reasoning


def test_detector_names_compatibility_reason_in_fallback(monkeypatch) -> None:
    error = ModelCompatibilityError(
        "Model artifact model.pkl was trained with scikit-learn 9.9.9 "
        "but the runtime is 1.5.2; refusing to unpickle across minor versions."
    )
    monkeypatch.setattr(
        "neurobridge.ml.detector.load_model",
        lambda: (_ for _ in ()).throw(error),
    )
    detector = ProfileDetector()

    events = [{"event_type": "chunk_dwell", "metadata": {"dwell_ms": 400, "scroll_speed": 1.3}}]
    result = detector.detect(events)

    assert result.fallback_to_quiz is True
    # The reasoning must carry the actual load failure so operators can tell
    # a broken artifact from a version mismatch that a retrain would fix.
    assert "9.9.9" in result.reasoning
    assert "refusing to unpickle" in result.reasoning


def test_save_model_records_training_metadata(tmp_path) -> None:
    model_path = tmp_path / "detector.pkl"
    report = train_model(per_profile=6, random_state=3, model_path=model_path)

    assert report.accuracy >= 0.0
    meta_path = tmp_path / "detector.pkl.meta.json"
    assert meta_path.exists()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["feature_count"] == 15
    assert meta["model_class"] == "RandomForestClassifier"
    assert meta["sklearn_version"]

    # A same-version load must succeed end to end.
    loaded = load_model(model_path)
    assert loaded is not None


def test_load_model_refuses_cross_minor_version(tmp_path) -> None:
    model_path = tmp_path / "detector.pkl"
    train_model(per_profile=6, random_state=3, model_path=model_path)

    meta_path = tmp_path / "detector.pkl.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["sklearn_version"] = "9.9.9"
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    with pytest.raises(ModelCompatibilityError) as excinfo:
        load_model(model_path)
    assert "9.9.9" in str(excinfo.value)


def test_load_model_accepts_same_minor_version(tmp_path) -> None:
    model_path = tmp_path / "detector.pkl"
    train_model(per_profile=6, random_state=3, model_path=model_path)

    meta_path = tmp_path / "detector.pkl.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    # Patch-level differences within the runtime's minor are accepted. Derive
    # the version instead of hardcoding one: CI resolves whatever the newest
    # satisfying scikit-learn is, which need not match the local pin.
    import sklearn

    major, minor = sklearn.__version__.split(".")[:2]
    meta["sklearn_version"] = f"{major}.{minor}.0"
    meta_path.write_text(json.dumps(meta), encoding="utf-8")

    assert load_model(model_path) is not None


def test_load_model_tolerates_legacy_artifact_without_metadata(tmp_path) -> None:
    model_path = tmp_path / "detector.pkl"
    train_model(per_profile=6, random_state=3, model_path=model_path)
    (tmp_path / "detector.pkl.meta.json").unlink()

    # Artifacts saved before metadata existed still load; save_model is the
    # component that guarantees new artifacts carry the version record.
    assert load_model(model_path) is not None
