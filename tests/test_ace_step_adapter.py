from main import parse_result, unwrap_data


def test_unwraps_current_ace_step_response_envelope():
    payload = {"data": {"task_id": "abc"}, "code": 200, "error": None}
    assert unwrap_data(payload) == {"task_id": "abc"}


def test_parses_current_query_result_json_string():
    result = '[{"file": "/v1/audio?path=/tmp/song.mp3", "metas": {"bpm": 120}}]'
    parsed = parse_result(result)
    assert parsed[0]["file"].startswith("/v1/audio?path=")
    assert parsed[0]["metas"]["bpm"] == 120


def test_parse_result_keeps_non_json_string():
    assert parse_result("not-json") == "not-json"


def test_unwrap_preserves_non_enveloped_values():
    assert unwrap_data([{"status": 0}]) == [{"status": 0}]
