import os
import sys
from pathlib import Path

os.environ["DEMO_MODE"] = "true"
os.environ["RATE_LIMIT_PER_MINUTE"] = "1000"

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient

from main import app, tasks

client = TestClient(app)


def setup_function():
    tasks.clear()


def test_home_and_config():
    home = client.get("/")
    assert home.status_code == 200
    assert "Yatharth Music AI" in home.text

    config = client.get("/api/config")
    assert config.status_code == 200
    body = config.json()
    assert body["demo_mode"] is True
    assert body["max_duration"] == 300
    assert "Hindi" in body["languages"]


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["demo_mode"] is True


def test_generate_poll_audio_and_delete():
    response = client.post("/api/generate", json={"prompt": "uplifting cinematic song"})
    assert response.status_code == 200
    created = response.json()
    task_id = created["task_id"]
    assert created["status"] == "completed"

    task = client.get(f"/api/tasks/{task_id}")
    assert task.status_code == 200
    assert task.json()["progress"] == 100
    assert task.json()["audio_url"] == f"/api/audio/{task_id}"

    audio = client.get(f"/api/audio/{task_id}")
    assert audio.status_code == 200
    assert audio.headers["content-type"].startswith("audio/wav")
    assert len(audio.content) > 100

    listing = client.get("/api/tasks")
    assert listing.status_code == 200
    assert any(item["task_id"] == task_id for item in listing.json())

    deleted = client.delete(f"/api/tasks/{task_id}")
    assert deleted.status_code == 200
    assert client.get(f"/api/tasks/{task_id}").status_code == 404


def test_task_status_and_audio_are_owner_only():
    owner = TestClient(app)
    other = TestClient(app)

    response = owner.post("/api/generate", json={"prompt": "private test song"})
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    # TestClient clients normally use the same host; override the request identity
    # with a forwarded address only when proxy trust is explicitly enabled.
    original = os.environ.get("TRUST_PROXY")
    os.environ["TRUST_PROXY"] = "true"
    try:
        assert owner.get(f"/api/tasks/{task_id}", headers={"X-Forwarded-For": "10.0.0.1"}).status_code == 200
        assert other.get(f"/api/tasks/{task_id}", headers={"X-Forwarded-For": "10.0.0.2"}).status_code == 403
        assert other.get(f"/api/audio/{task_id}", headers={"X-Forwarded-For": "10.0.0.2"}).status_code == 403
        assert owner.get(f"/api/audio/{task_id}", headers={"X-Forwarded-For": "10.0.0.1"}).status_code == 200
    finally:
        if original is None:
            os.environ.pop("TRUST_PROXY", None)
        else:
            os.environ["TRUST_PROXY"] = original


def test_generation_validation():
    empty = client.post("/api/generate", json={"prompt": "", "lyrics": "", "instrumental": False})
    assert empty.status_code == 400

    bad_format = client.post("/api/generate", json={"prompt": "test", "format": "ogg"})
    assert bad_format.status_code == 422

    bad_duration = client.post("/api/generate", json={"prompt": "test", "duration": 301})
    assert bad_duration.status_code == 422


def test_random_sample_and_format_input_in_demo_mode():
    sample = client.post("/api/random-sample")
    assert sample.status_code == 200
    assert sample.json()["ok"] is True
    assert "caption" in sample.json()["data"]

    formatted = client.post("/api/format-input", json={"prompt": "  hello world  "})
    assert formatted.status_code == 200
    assert formatted.json()["text"] == "hello world"


def test_security_headers():
    response = client.get("/api/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
