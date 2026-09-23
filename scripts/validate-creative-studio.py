import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "production-manifest.json").read_text(encoding="utf-8"))
main = (ROOT / "main.py").read_text(encoding="utf-8")
studio = (ROOT / "studio.js").read_text(encoding="utf-8")

required_agents = {a["id"] for a in manifest["agents"]}
required_contracts = ["/api/studio/plan", "/api/studio/status", "/api/studio/manifest", "/api/studio/run", "/api/studio/runs/{run_id}", "/api/studio/runs/{run_id}/manifest", "/api/studio/runs/{run_id}/artifacts/{artifact_name}", "StudioPlanRequest", "StudioPlanResponse"]
assert manifest["schema_version"] == 1
assert manifest["policy"]["no_secret_exposure"] is True
assert manifest["policy"]["no_fabricated_rendering_claims"] is True
assert all(agent in main for agent in required_agents)
assert all(token in main for token in required_contracts)
assert 'fetch("/api/studio/plan"' in studio
ast.parse(main)
print("creative-studio contract validation: PASS")
assert 'fetch("/api/studio/plan"' in studio
assert 'fetch("/api/studio/run"' in studio
assert 'fetch("/api/studio/runs/"+encodeURIComponent(activeRunId)' in studio
html = (ROOT / "studio.html").read_text(encoding="utf-8")
assert 'id="runProduction"' in html
assert 'id="productionRun"' in html
assert 'id="downloadManifest"' in html

assert 'encodeURIComponent(activeRunId)+\"/artifacts/\"' in studio
assert "function viewArtifact" in studio
assert "function downloadArtifact" in studio
assert "artifact-open" in studio
print("creative-studio artifact contract validation: PASS")
