"""Day 5 tests for memory stores and feedback learning flow."""

from concurrent.futures import ThreadPoolExecutor

from neurobridge import Config, NeuroBridge, Profile
from neurobridge.core.memory import FeedbackAnalyser, SQLiteMemoryStore, create_feedback_record
from neurobridge.core.profile import get_profile_config


def test_sqlite_memory_store_save_load_feedback_clear(tmp_path) -> None:
    db_path = tmp_path / "memory.db"
    store = SQLiteMemoryStore(str(db_path))

    user_id = "u-1"
    profile = get_profile_config(Profile.ADHD)
    store.save_profile(user_id, profile)

    loaded = store.load_profile(user_id)
    assert loaded is not None
    assert loaded.chunk_size == profile.chunk_size

    record = create_feedback_record(
        user_id=user_id,
        original_text="Original text",
        adapted_text="Adapted text",
        user_edit="Edited text",
    )
    store.save_feedback(record)
    feedback = store.get_feedback(user_id)
    assert len(feedback) == 1
    assert len(feedback[0].user_edit_hash) == 64
    assert len(feedback[0].original_hash) == 64
    assert len(feedback[0].adapted_hash) == 64

    store.clear_user_data(user_id)
    assert store.load_profile(user_id) is None
    assert store.get_feedback(user_id) == []

    store.close()


def test_inmemory_store_via_neurobridge_feedback_learning(tmp_path) -> None:
    db_path = tmp_path / "bridge-memory.db"
    bridge = NeuroBridge(
        config=Config(memory_backend="sqlite", memory_path=str(db_path), auto_adjust_after=2)
    )
    bridge.set_profile(Profile.ANXIETY)

    first = bridge.chat("Please explain deployment steps.", user_id="user-x")
    bridge.submit_feedback(
        original_text=first.raw_text,
        adapted_text=first.adapted_text,
        user_edit="Shorter and calmer steps please.",
        user_id="user-x",
    )

    second = bridge.chat("Explain rollback steps.", user_id="user-x")
    assert second.adapted_text


def test_feedback_analyser_returns_adjustments(tmp_path) -> None:
    db_path = tmp_path / "analysis.db"
    store = SQLiteMemoryStore(str(db_path))
    user_id = "u-2"
    profile = get_profile_config(Profile.ADHD)
    store.save_profile(user_id, profile)

    for _ in range(4):
        record = create_feedback_record(
            user_id=user_id,
            original_text="Long and urgent original output.",
            adapted_text="Urgent response with many details and critical timeline.",
            user_edit="Short calm version.",
        )
        store.save_feedback(record)

    adjustments = FeedbackAnalyser().analyse_feedback(user_id, store)
    assert adjustments.chunk_size_delta <= 0
    assert adjustments.max_sentence_words_delta <= 0
    assert adjustments.reason

    store.close()


def test_sqlite_memory_store_thread_safety_concurrent_writes(tmp_path) -> None:
    db_path = tmp_path / "concurrent.db"
    store = SQLiteMemoryStore(str(db_path))
    user_id = "u-thread"

    def worker(index: int) -> None:
        record = create_feedback_record(
            user_id=user_id,
            original_text=f"original {index}",
            adapted_text=f"adapted {index}",
            user_edit=f"edit {index}",
        )
        store.save_feedback(record)
        store.increment_interaction(user_id)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(worker, range(40)))

    feedback = store.get_feedback(user_id)
    assert len(feedback) == 40
    assert store.get_interaction_count(user_id) == 40

    store.close()
