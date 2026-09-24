import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / "production-manifest.json").read_text(encoding="utf-8"))
federation = json.loads((ROOT / "federation/creative-studio-contract.json").read_text(encoding="utf-8"))
main = (ROOT / "main.py").read_text(encoding="utf-8")
studio = (ROOT / "studio.js").read_text(encoding="utf-8")

required_agents = {a["id"] for a in manifest["agents"]}
required_contracts = ["/api/studio/plan", "/api/studio/status", "/api/studio/manifest", "/api/studio/run", "/api/studio/runs/{run_id}", "/api/studio/runs/{run_id}/manifest", "/api/studio/runs/{run_id}/artifacts/{artifact_name}", "/api/studio/runs/{run_id}/music-task", "StudioPlanRequest", "StudioPlanResponse"]
assert manifest["schema_version"] == 1
assert manifest["policy"]["no_secret_exposure"] is True
assert manifest["policy"]["no_fabricated_rendering_claims"] is True
assert federation["source_repository"] == manifest["federation"]["source_repository"]
assert federation["target_repository"] == "rampaulsaini/yatharth-music-ai"
assert federation["event_type"] == "yatharth_studio_request"
assert federation["accepted_formats"] == manifest["federation"]["approved_formats"]
assert federation["policy"]["approved_source_only"] is True
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
assert "stages/{stage}/execute" in main
assert "artifact-open" in studio
print("creative-studio artifact contract validation: PASS")

assert "lyrics=request.lyrics" in main
assert '"client_id": client_id(http_request)' in main
assert "def _studio_owner" in main
assert "_public_studio_run" in main
assert "_prune_studio_runs" in main
assert "MAX_STUDIO_RUNS_IN_MEMORY" in main
assert 'return _public_studio_run(run)\n\n\n@app.get("/api/studio/runs/{run_id}/artifacts/{artifact_name}")' in main
assert 'if safe_name == "production-manifest.json":\n        return _public_studio_run(run)' in main
assert 'fetch("/api/studio/runs/"+encodeURIComponent(activeRunId)+"/music-task"' in studio


# Browser runtime syntax is part of the production contract.
import subprocess
subprocess.run(["node", "--check", str(ROOT / "studio.js")], check=True)
print("studio.js syntax validation: PASS")
assert "yatharth_studio_request" in (ROOT / ".github/workflows/shirmani-federation-intake.yml").read_text(encoding="utf-8")
assert "source_repository" in (ROOT / ".github/workflows/shirmani-federation-intake.yml").read_text(encoding="utf-8")
print("Shirmani federation contract validation: PASS")
