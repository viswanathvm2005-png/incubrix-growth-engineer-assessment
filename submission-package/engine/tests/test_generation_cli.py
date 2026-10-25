import json

from engine.__main__ import main


def make_brief(path, content_format="static_post"):
    brief = {
        "brief_id": "test-brief-001",
        "campaign_objective": "Test the generation CLI",
        "target_audience": "Assessment reviewer",
        "platform": "linkedin",
        "content_format": content_format,
        "source_ids": ["test-source-placeholder"],
        "capability_ids": [],
        "key_message": "A clearly labelled sample message",
        "tone": "professional",
        "call_to_action": "Review the sample",
        "avoid_topics": [],
    }

    if content_format == "short_video":
        brief["requested_duration_seconds"] = 30
        brief["aspect_ratio"] = "9:16"

    path.write_text(json.dumps(brief), encoding="utf-8")
    return path


def test_generate_cli_returns_labelled_mock_drafts(tmp_path, capsys):
    brief_path = make_brief(tmp_path / "brief.json")

    exit_code = main([
        "generate",
        "--brief", str(brief_path),
        "--request-id", "test-request-001",
        "--draft-count", "2",
    ])

    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["brief_id"] == "test-brief-001"
    assert output["status"] == "success"
    assert len(output["drafts"]) == 2
    assert output["provider_name"] == "mock"
    assert "MOCK OUTPUT ONLY" in output["warnings"][0]
    assert all(
        "[MOCK CONTENT" in draft["caption"]
        for draft in output["drafts"]
    )


def test_generate_cli_rejects_missing_brief(tmp_path, capsys):
    missing_path = tmp_path / "missing.json"

    exit_code = main([
        "generate",
        "--brief", str(missing_path),
    ])

    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["status"] == "ERROR"


def test_generate_cli_rejects_invalid_brief(tmp_path, capsys):
    brief_path = tmp_path / "invalid.json"
    brief_path.write_text('{"unexpected_field": true}', encoding="utf-8")

    exit_code = main([
        "generate",
        "--brief", str(brief_path),
    ])

    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["status"] == "ERROR"


def test_generate_cli_creates_video_script_for_short_video(tmp_path, capsys):
    brief_path = make_brief(
        tmp_path / "video-brief.json",
        content_format="short_video",
    )

    exit_code = main([
        "generate",
        "--brief", str(brief_path),
        "--draft-count", "1",
    ])

    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert len(output["drafts"]) == 1
    assert output["drafts"][0]["video_script"]
    assert "MOCK OUTPUT ONLY" in output["warnings"][0]


def test_generate_cli_rejects_unapproved_capability(tmp_path, capsys):
    brief_path = tmp_path / "claim-brief.json"
    brief = {
        "brief_id": "claim-brief-001",
        "campaign_objective": "Test capability authorization",
        "target_audience": "Assessment reviewer",
        "platform": "linkedin",
        "content_format": "static_post",
        "source_ids": ["test-source-placeholder"],
        "capability_ids": ["capability-001"],
        "key_message": "Test message",
        "tone": "professional",
        "call_to_action": "Review",
        "avoid_topics": [],
    }
    brief_path.write_text(json.dumps(brief), encoding="utf-8")

    exit_code = main([
        "generate",
        "--brief", str(brief_path),
    ])

    output = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert output["status"] == "ERROR"
    assert "capability-001" in output["message"]
