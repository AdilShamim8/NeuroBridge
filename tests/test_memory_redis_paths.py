"""Targeted RedisMemoryStore branch tests using fake redis clients."""

from __future__ import annotations

from dataclasses import asdict

from neurobridge.core.memory import (
    FeedbackRecord,
    InMemoryStore,
    RedisMemoryStore,
    create_feedback_record,
)
from neurobridge.core.profile import Profile, get_profile_config


class _FakePipeline:
    def __init__(self, store: dict[str, object], fail: bool = False) -> None:
        self._store = store
        self._ops: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
        self._fail = fail

    def set(self, key: str, value: str, ex: int | None = None):
        self._ops.append(("set", (key, value), {"ex": ex}))
        return self

    def rpush(self, key: str, value: str):
        self._ops.append(("rpush", (key, value), {}))
        return self

    def get(self, key: str):
        self._ops.append(("get", (key,), {}))
        return self

    def execute(self):
        if self._fail:
            raise RuntimeError("pipeline failure")

        out: list[object] = []
        for op, args, kwargs in self._ops:
            if op == "set":
                key, value = args
                self._store[str(key)] = value
                out.append(True)
            elif op == "rpush":
                key, value = args
                seq = self._store.setdefault(str(key), [])
                assert isinstance(seq, list)
                seq.append(value)
                out.append(len(seq))
            elif op == "get":
                (key,) = args
                out.append(self._store.get(str(key)))

        self._ops.clear()
        return out


class _FakeRedis:
    def __init__(self, fail_pipeline: bool = False, fail_get: bool = False) -> None:
        self.data: dict[str, object] = {}
        self._fail_pipeline = fail_pipeline
        self._fail_get = fail_get
        self.deleted: list[str] = []

    def pipeline(self, transaction: bool = True):
        _ = transaction
        return _FakePipeline(self.data, fail=self._fail_pipeline)

    def get(self, key: str):
        if self._fail_get:
            raise RuntimeError("get failure")
        return self.data.get(key)

    def lrange(self, key: str, start: int, end: int):
        _ = start, end
        seq = self.data.get(key, [])
        return list(seq) if isinstance(seq, list) else []

    def incr(self, key: str):
        value = int(self.data.get(key, 0)) + 1
        self.data[key] = value
        return value

    def delete(self, *keys: str):
        for key in keys:
            self.deleted.append(key)
            self.data.pop(key, None)


class _FakePool:
    def __init__(self, fail_disconnect: bool = False) -> None:
        self.disconnected = False
        self._fail_disconnect = fail_disconnect

    def disconnect(self):
        if self._fail_disconnect:
            raise RuntimeError("disconnect failure")
        self.disconnected = True


def test_redis_store_happy_path_with_fake_client() -> None:
    store = RedisMemoryStore("redis://localhost:1", fallback_store=InMemoryStore())
    fake = _FakeRedis()
    store._redis = fake  # noqa: SLF001
    store._pool = _FakePool()  # noqa: SLF001

    profile = get_profile_config(Profile.ADHD)
    store.save_profile("u1", profile)
    loaded = store.load_profile("u1")
    assert loaded is not None
    assert asdict(loaded) == asdict(profile)

    record = create_feedback_record("u1", "original text", "adapted text", "edited text")
    store.save_feedback(record)
    history = store.get_feedback("u1")
    assert history
    assert isinstance(history[0], FeedbackRecord)

    assert store.increment_interaction("u1") == 1
    assert store.get_interaction_count("u1") == 1

    store.clear_user_data("u1")
    assert store.load_profile("u1") is None

    store.close()
    assert store._pool.disconnected is True  # type: ignore[union-attr]  # noqa: SLF001


def test_redis_store_gracefully_handles_backend_failures() -> None:
    fallback = InMemoryStore()
    store = RedisMemoryStore("redis://localhost:1", fallback_store=fallback)
    profile = get_profile_config(Profile.DYSLEXIA)
    fallback.save_profile("u2", profile)

    store._redis = _FakeRedis(fail_pipeline=True, fail_get=True)  # noqa: SLF001
    store._pool = _FakePool(fail_disconnect=True)  # noqa: SLF001

    store.save_profile("u2", profile)
    loaded = store.load_profile("u2")
    assert loaded is not None
    assert asdict(loaded) == asdict(profile)

    record = create_feedback_record("u2", "o", "a", "e")
    store.save_feedback(record)
    # get_feedback should fall back when redis get/lrange path fails.
    history = store.get_feedback("u2")
    assert history

    assert store.increment_interaction("u2") == 1
    assert store.get_interaction_count("u2") == 1

    # Should not raise even when backend delete/disconnect fail.
    store.clear_user_data("u2")
    store.close()
