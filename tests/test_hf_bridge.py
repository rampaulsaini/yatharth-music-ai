import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
HF_SPACE = ROOT / "hf_space"
if str(HF_SPACE) not in sys.path:
    sys.path.insert(0, str(HF_SPACE))

from bridge import YatharthAPIError, YatharthBridge


def test_absolute_url_handles_relative_and_absolute_paths():
    bridge = YatharthBridge("https://api.example.com/")
    assert bridge.absolute_url("/api/tasks/abc") == "https://api.example.com/api/tasks/abc"
    assert bridge.absolute_url("https://cdn.example.com/song.wav") == "https://cdn.example.com/song.wav"


def test_generate_sends_expected_payload(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"task_id": "abc", "status": "queued"}

    def fake_request(method, url, **kwargs):
        captured.update(method=method, url=url, kwargs=kwargs)
        return FakeResponse()

    monkeypatch.setattr(httpx, "request", fake_request)
    result = YatharthBridge("https://api.example.com", token="secret").generate(prompt="hello")

    assert result["task_id"] == "abc"
    assert captured["method"] == "POST"
    assert captured["url"] == "https://api.example.com/api/generate"
    assert captured["kwargs"]["json"] == {"prompt": "hello"}
    assert captured["kwargs"]["headers"]["Authorization"] == "Bearer secret"


def test_non_object_response_raises(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return ["unexpected"]

    monkeypatch.setattr(httpx, "request", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(YatharthAPIError):
        YatharthBridge("https://api.example.com").health()
