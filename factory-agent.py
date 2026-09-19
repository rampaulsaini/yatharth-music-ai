#!/usr/bin/env python3
"""Deterministic, free-first specialist agent.
It does not call a paid AI API and never executes discovered repository code.
It inventories text/source files and writes a traceable readiness manifest.
"""
from pathlib import Path
import hashlib, json, os, datetime

ROOT=Path(".")
CFG=ROOT/"factory-agent.json"
OUT=ROOT/"agent-output"
OUT.mkdir(exist_ok=True)
cfg=json.loads(CFG.read_text(encoding="utf-8"))
allowed={".md",".txt",".html",".htm",".json",".yml",".yaml",".py",".js",".ts",".css"}
skip={".git","node_modules","venv",".venv","agent-output"}
files=[]
for p in ROOT.rglob("*"):
    if p.is_file() and p.suffix.lower() in allowed and not any(part in skip for part in p.parts):
        try:
            data=p.read_bytes()
            files.append({"path":str(p.as_posix()),"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
        except Exception:
            pass
files.sort(key=lambda x:x["path"])
payload={
 "schema_version":1,
 "generated_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),
 "repository":cfg["repo"],
 "role":cfg["role"],
 "mode":cfg["mode"],
 "ai_provider":cfg["ai_provider"],
 "source_count":len(files),
 "sources":files,
 "policy":cfg["policy"],
 "status":"ready",
 "note":"This is an automation/readiness agent, not a claim of autonomous scientific intelligence."
}
blob=json.dumps(payload,ensure_ascii=False,indent=2)+"\n"
(OUT/"manifest.json").write_text(blob,encoding="utf-8")
print(f"Agent ready: {cfg['role']} | sources={len(files)}")
