"""Unit tests for engine.asset_audit and engine.rights_inventory."""
from __future__ import annotations

import struct
from pathlib import Path

from engine.asset_audit import NEGATED, PERFORMANCE, audit, png_size, select_audit_sample
from engine.rights_inventory import inventory, scan_html


def test_select_audit_sample_is_deterministic():
    ids = [f"ASSET-{i:02d}" for i in range(1, 31)]
    first = select_audit_sample(ids, "incubrix-audit-2026-10-25", size=20)
    second = select_audit_sample(list(reversed(ids)), "incubrix-audit-2026-10-25", size=20)
    assert len(first) == 20
    assert first == second


def test_png_size_reads_valid_header_and_rejects_non_png(tmp_path: Path):
    png = tmp_path / "sample.png"
    ihdr = struct.pack(">II", 1080, 1350) + b"\x08\x02\x00\x00\x00"
    png.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + ihdr)
    assert png_size(png) == (1080, 1350)

    bad = tmp_path / "not.png"
    bad.write_bytes(b"not a png file")
    assert png_size(bad) is None


def test_negated_guarantee_disclaimers_do_not_trigger_performance_regex():
    disclaimer_1 = "Different formats serve different purposes, not guaranteed performance outcomes."
    disclaimer_2 = "A checklist cannot guarantee results, but it can make your review process more consistent."
    assert PERFORMANCE.findall(NEGATED.sub(" ", disclaimer_1)) == []
    assert PERFORMANCE.findall(NEGATED.sub(" ", disclaimer_2)) == []

    positive_claim = "This workflow will guarantee 3x engagement."
    assert len(PERFORMANCE.findall(NEGATED.sub(" ", positive_claim))) >= 1


def test_scan_html_extracts_non_generic_fonts_and_urls(tmp_path: Path):
    html = tmp_path / "slide.html"
    html.write_text(
        "<style>body { font-family: 'Segoe UI', Arial, sans-serif; }</style>"
        "<script src='https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js'></script>"
        "<img src='assets/logo.png'>",
        encoding="utf-8",
    )
    info = scan_html(html)
    assert info["fonts"] == {"Segoe UI", "Arial"}
    assert "https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js" in info["urls"]
    assert "assets/logo.png" in info["images"]


def test_rights_inventory_keeps_all_assets_pending_human_review():
    root = Path(__file__).resolve().parent.parent
    rows = inventory(root)
    assert len(rows) == 30
    assert all(r["rights_status"] == "PENDING HUMAN REVIEW" for r in rows)


def test_repo_asset_audit_runs_and_preserves_ready_to_publish_zero():
    root = Path(__file__).resolve().parent.parent
    res = audit(root)
    assert res["totals"]["assets"] == 30
    assert res["totals"]["automated_pass"] == 30
    assert res["random_sample"]["automated_pass_rate"] == "20/20"
    assert res["totals"]["ready_to_publish"] == 0
    assert all(c["result"] == "PASS" for c in res["global_checks"])
