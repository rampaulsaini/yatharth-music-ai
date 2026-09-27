import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_platform_manifest_has_safe_upgrade_policy():
    data = json.loads((ROOT / "platform" / "PLATFORM_MANIFEST.json").read_text(encoding="utf-8"))
    assert data["availability_goal"] == "24/7/365"
    assert data["upgrade_policy"]["automatic_production_code_changes"] is False
    assert "human-approval" in data["upgrade_policy"]["required_gates"]


def test_health_supervisor_is_bounded_and_not_self_modifying():
    source = (ROOT / "scripts" / "health-supervisor.py").read_text(encoding="utf-8")
    assert "replace_or_restart" in source
    assert "automatic production code changes" not in source.lower()
