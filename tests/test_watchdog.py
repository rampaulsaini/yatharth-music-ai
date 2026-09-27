import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import process_watchdog

def test_missing_health_endpoint_is_unhealthy():
    assert process_watchdog.healthy("http://127.0.0.1:9/not-running", 0.2) is False
