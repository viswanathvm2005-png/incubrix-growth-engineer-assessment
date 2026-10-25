import json

from engine.__main__ import main
from engine.schemas import AssetFormat, ContentAsset, Platform


def write_asset(path, *, asset_id="cli-asset-001", version=1, hook="Sample hook",
                caption="Sample caption for a CLI history test."):
    asset = ContentAsset(
        asset_id=asset_id,
        version=version,
        source_id="cli-source-001",
        platform=Platform.LINKEDIN,
        format=AssetFormat.TEXT,
        angle="educational explanation",
        hook=hook,
        caption=caption,
        cta="Learn more",
        utm_url="https://example.com/?utm_source=cli_test",
        target_metric="clicks",
        created_by_run_id=f"cli-run-{version}",
    )
    path.write_text(
        json.dumps(asset.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    return path


def test_history_save_and_show_commands(tmp_path, capsys):
    asset_path = write_asset(tmp_path / "asset.json")
    database = tmp_path / "history.sqlite3"

    save_code = main([
        "history", "save", "--asset", str(asset_path),
        "--database", str(database),
    ])
    save_output = json.loads(capsys.readouterr().out)

    show_code = main([
        "history", "show", "--asset-id", "cli-asset-001",
        "--database", str(database),
    ])
    show_output = json.loads(capsys.readouterr().out)

    assert save_code == 0
    assert save_output["status"] == "SAVED"
    assert show_code == 0
    assert show_output["status"] == "FOUND"
    assert len(show_output["versions"]) == 1


def test_history_revise_appends_next_version(tmp_path, capsys):
    database = tmp_path / "history.sqlite3"
    first = write_asset(tmp_path / "first.json", version=1)
    second = write_asset(
        tmp_path / "second.json",
        version=2,
        hook="A revised sample hook",
    )

    assert main([
        "history", "save", "--asset", str(first),
        "--database", str(database),
    ]) == 0
    capsys.readouterr()

    assert main([
        "history", "revise", "--asset", str(second),
        "--database", str(database),
    ]) == 0
    revised_output = json.loads(capsys.readouterr().out)

    assert revised_output["status"] == "SAVED"
    assert revised_output["version"] == 2


def test_history_revise_rejects_missing_prior_version(tmp_path, capsys):
    asset_path = write_asset(tmp_path / "asset.json", version=2)

    code = main([
        "history", "revise", "--asset", str(asset_path),
        "--database", str(tmp_path / "history.sqlite3"),
    ])
    output = json.loads(capsys.readouterr().out)

    assert code == 1
    assert output["status"] == "ERROR"
    assert "no saved history" in output["message"]


def test_history_duplicates_command_flags_similar_content(tmp_path, capsys):
    database = tmp_path / "history.sqlite3"
    original = write_asset(tmp_path / "original.json")

    assert main([
        "history", "save", "--asset", str(original),
        "--database", str(database),
    ]) == 0
    capsys.readouterr()

    candidate = write_asset(
        tmp_path / "candidate.json",
        asset_id="cli-asset-002",
        hook="Sample hook",
        caption="Sample caption for a CLI history test.",
    )
    code = main([
        "history", "duplicates", "--asset", str(candidate),
        "--database", str(database),
    ])
    output = json.loads(capsys.readouterr().out)

    assert code == 0
    assert output["status"] == "REVIEW_REQUIRED"
    assert output["matches"][0]["asset_id"] == "cli-asset-001"


def test_history_save_rejects_invalid_json_schema(tmp_path, capsys):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text('{"asset_id": "missing fields"}', encoding="utf-8")

    code = main([
        "history", "save", "--asset", str(bad_file),
        "--database", str(tmp_path / "history.sqlite3"),
    ])
    output = json.loads(capsys.readouterr().out)

    assert code == 1
    assert output["status"] == "ERROR"
    assert "ContentAsset schema" in output["message"]
