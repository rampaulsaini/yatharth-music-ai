"""Quick local diagnostic for Yatharth Music AI and ACE-Step."""

import os
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen

YATHARTH_URL = os.getenv("YATHARTH_URL", "http://127.0.0.1:8000")
ENGINE_URL = os.getenv("MUSIC_ENGINE_URL", "http://127.0.0.1:8001")


def check(name: str, url: str) -> bool:
    try:
        request = Request(url, headers={"Accept": "application/json"})
        with urlopen(request, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
            print(f"[OK] {name}: HTTP {response.status}")
            print(body[:500])
            return 200 <= response.status < 400
    except (URLError, TimeoutError, OSError) as exc:
        print(f"[FAIL] {name}: {exc}")
        return False


print("Yatharth Music AI - local engine diagnostic")
print("=" * 48)
yatharth_ok = check("Yatharth backend", f"{YATHARTH_URL}/api/health")
engine_ok = check("ACE-Step engine", f"{ENGINE_URL}/health")
print("=" * 48)
if yatharth_ok and engine_ok:
    print("READY: Yatharth and ACE-Step are both reachable.")
    sys.exit(0)
if yatharth_ok:
    print("PARTIAL: Yatharth is running, but ACE-Step is not reachable.")
else:
    print("NOT READY: Start Yatharth first, then run this diagnostic again.")
sys.exit(1)
