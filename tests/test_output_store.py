import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from engine.output_store import save_generation_result


def sample_result():
    return {
        "brief_id": "sample-brief-001",
        "status": "success",
        "drafts": [
            {
                "draft_id": "draft-001",
                "content_format": "static_post",
                "angle": "Explain the sample workflow",
                "hook": "See how a sample brief becomes a draft.",
                "caption": "This is sample content for review.",
                "call_to_action": "Review the prototype output",
                "hashtags": ["#sample", "#workflow"],
                "product_claims": [],
                "video_script": None,
            }
        ],
        "warnings": ["Human review required"],
        "provider_name": "mock",
        "model_name": "deterministic-test-provider",
    }


def test_save_generation_result_writes_valid_json(tmp_path):
    result = sample_result()

    saved = save_generation_result(result, tmp_path)

    path = tmp_path / "sample-brief-001-mock.json"
    assert saved["saved"] is True
    assert path.is_file()
    assert json.loads(path.read_text(encoding="utf-8")) == result


def test_save_generation_result_does_not_overwrite(tmp_path):
    first = save_generation_result(sample_result(), tmp_path)
    second = save_generation_result(sample_result(), tmp_path)

    assert first["path"] != second["path"]
    assert (tmp_path / "sample-brief-001-mock.json").is_file()
    assert (tmp_path / "sample-brief-001-mock-2.json").is_file()


def test_save_generation_result_rejects_failed_result(tmp_path):
    result = sample_result()
    result["status"] = "failed"
    result["drafts"] = []

    with pytest.raises(ValueError, match="Only successful"):
        save_generation_result(result, tmp_path)

    assert list(tmp_path.glob("*.json")) == []


def test_save_generation_result_rejects_missing_brief_id(tmp_path):
    result = sample_result()
    result["brief_id"] = ""

    with pytest.raises(ValidationError, match="brief_id"):
        save_generation_result(result, tmp_path)

    assert list(tmp_path.glob("*.json")) == []


def test_save_generation_result_rejects_malformed_draft(tmp_path):
    result = sample_result()
    del result["drafts"][0]["caption"]

    with pytest.raises(ValidationError):
        save_generation_result(result, tmp_path)

    assert list(tmp_path.glob("*.json")) == []


def test_save_generation_result_rejects_unknown_fields(tmp_path):
    result = sample_result()
    result["unexpected_field"] = "should not be accepted"

    with pytest.raises(ValidationError):
        save_generation_result(result, tmp_path)

    assert list(tmp_path.glob("*.json")) == []


def test_save_generation_result_rejects_non_dictionary(tmp_path):
    with pytest.raises(ValueError, match="JSON object"):
        save_generation_result([], tmp_path)

    assert list(tmp_path.glob("*.json")) == []


def test_save_generation_result_sanitizes_filename(tmp_path):
    result = sample_result()
    result["brief_id"] = "../../unsafe/name"

    saved = save_generation_result(result, tmp_path)

    assert saved["saved"] is True
    assert len(list(tmp_path.glob("*.json"))) == 1
    assert ".." not in Path(saved["path"]).name
    assert Path(saved["path"]).parent == tmp_path


def test_save_generation_result_handles_missing_provider(tmp_path):
    result = sample_result()
    result["provider_name"] = None

    saved = save_generation_result(result, tmp_path)

    assert saved["saved"] is True
    assert Path(saved["path"]).name == (
        "sample-brief-001-unknown-provider.json"
    )
