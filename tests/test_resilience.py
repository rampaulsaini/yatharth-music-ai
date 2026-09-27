from pathlib import Path
import tempfile

def test_resilience_state_round_trip():
    import resilience
    old = resilience.DB_PATH
    with tempfile.TemporaryDirectory() as tmp:
        resilience.DB_PATH = Path(tmp) / "state.sqlite3"
        resilience.init_state()
        class R:
            id="t1"; client_id="c1"; request=type("Req",(),{"model_dump_json":lambda self:'{"prompt":"x"}'})()
            status="queued"; progress=0; audio_url=None; metadata={}; error=None; created=1.0
            engine_task_id=None; engine_file=None; attempts=0; next_attempt=0
        resilience.save_task(R())
        assert resilience.load_tasks()[0]["task_id"]=="t1"
        resilience.delete_task("t1")
        assert resilience.load_tasks()==[]
    resilience.DB_PATH=old

def test_recovery_marks_interrupted_work():
    import resilience
    old=resilience.DB_PATH
    with tempfile.TemporaryDirectory() as tmp:
        resilience.DB_PATH=Path(tmp)/"state.sqlite3"
        resilience.init_state()
        class R:
            id="t2"; client_id="c1"; request=type("Req",(),{"model_dump_json":lambda self:'{"prompt":"x"}'})()
            status="processing"; progress=10; audio_url=None; metadata={}; error=None; created=1.0
            engine_task_id="e"; engine_file=None; attempts=1; next_attempt=0
        resilience.save_task(R())
        assert resilience.recover_inflight()==1
        assert resilience.load_tasks()[0]["status"]=="queued"
    resilience.DB_PATH=old
