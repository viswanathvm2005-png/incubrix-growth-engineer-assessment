"""Tests for engine.package_verify."""
from pathlib import Path

from engine.package_verify import verify

ROOT = Path(__file__).resolve().parents[1]


def test_package_verify_passes_on_repository():
    report = verify(ROOT)
    assert report["status"] == "OK", report["problems"]
    assert report["official_workbook_hash_ok"] is True
    assert report["formula_overwrites"] == []
    assert all(s["package_sha256_equal"] for s in report["shorts"])
