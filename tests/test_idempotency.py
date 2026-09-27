from pathlib import Path

import resilience


def test_idempotency_binding_is_atomic(tmp_path, monkeypatch):
    db = tmp_path / "state.sqlite3"
    monkeypatch.setattr(resilience, "DB_PATH", Path(db))
    resilience.init_state()

    assert resilience.find_idempotent_task("client-a", "request-1") is None
    assert resilience.bind_idempotency("client-a", "request-1", "task-1") is True
    assert resilience.find_idempotent_task("client-a", "request-1") == "task-1"

    # A duplicate retry must never replace the original task.
    assert resilience.bind_idempotency("client-a", "request-1", "task-2") is False
    assert resilience.find_idempotent_task("client-a", "request-1") == "task-1"

    # Different clients may legitimately reuse the same key.
    assert resilience.bind_idempotency("client-b", "request-1", "task-3") is True
    assert resilience.find_idempotent_task("client-b", "request-1") == "task-3"
