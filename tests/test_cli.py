from engine.__main__ import main


def test_cli_accepts_valid_source(tmp_path, capsys):
    source = tmp_path / "sample.md"
    source.write_text("# Notes\nCandidate text.\n", encoding="utf-8")

    exit_code = main([
        "intake",
        "--input", str(source),
        "--source-id", "cli-001",
    ])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"status": "ACCEPTED"' in output
    assert '"source_id": "cli-001"' in output


def test_cli_rejects_missing_source(tmp_path, capsys):
    exit_code = main([
        "intake",
        "--input", str(tmp_path / "missing.md"),
        "--source-id", "cli-002",
    ])

    output = capsys.readouterr().out

    assert exit_code == 1
    assert '"status": "REJECTED"' in output


def test_cli_respects_size_limit(tmp_path, capsys):
    source = tmp_path / "sample.txt"
    source.write_text("1234567890", encoding="utf-8")

    exit_code = main([
        "intake",
        "--input", str(source),
        "--source-id", "cli-003",
        "--max-bytes", "5",
    ])

    output = capsys.readouterr().out

    assert exit_code == 1
    assert '"status": "REJECTED"' in output
