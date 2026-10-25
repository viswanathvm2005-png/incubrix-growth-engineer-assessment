"""Inventory the media/font/third-party references that need rights review.

This only DETECTS what files reference (fonts, external URLs, images, audio).
It never decides that anything is licensed or cleared: every row stays
`PENDING HUMAN REVIEW` until a person records evidence.

Run: py -3.12 -m engine.rights_inventory
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

FONT_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.I)
URL_RE = re.compile(r"https?://[^\s\"')>]+", re.I)
IMG_RE = re.compile(r"<img\b[^>]*src=[\"']([^\"']+)[\"']", re.I)
CSS_URL_RE = re.compile(r"url\(\s*[\"']?([^\"')]+)[\"']?\s*\)", re.I)
FONT_FILE_RE = re.compile(r"@font-face|\.(?:woff2?|ttf|otf)\b", re.I)
AV_RE = re.compile(r"<(?:audio|video|source)\b|\.(?:mp3|wav|m4a|mp4)\b", re.I)
GENERIC_FONTS = {"sans-serif", "serif", "monospace", "system-ui", "cursive", "inherit"}
COLUMNS = [
    "asset_id", "platform", "scanned_files", "fonts_referenced", "external_urls", "images_or_css_urls",
    "font_files_or_font_face", "audio_video_refs", "audio_track_in_final_file", "voice_source",
    "music_source", "visual_source", "rights_status", "ai_label_decision", "required_evidence",
]


def scan_html(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    fonts: set[str] = set()
    for match in FONT_RE.findall(text):
        for name in match.split(","):
            name = name.strip().strip("'\"")
            if name and name.lower() not in GENERIC_FONTS:
                fonts.add(name)
    urls = {u.rstrip(".,;") for u in URL_RE.findall(text)}
    imgs = set(IMG_RE.findall(text)) | {u for u in CSS_URL_RE.findall(text) if ("/" in u or "." in u) and not u.startswith(("data:", "blob:"))}
    return {"fonts": fonts, "urls": urls, "images": imgs,
            "font_face": bool(FONT_FILE_RE.search(text)), "av": bool(AV_RE.search(text))}


def inventory(root: str | Path = ".", calendar: str = "calendar.csv",
              canonical: str = "content/canonical-sources.csv") -> list[dict]:
    root = Path(root)
    cal_path = (root / "calendar_UPDATED.csv") if (root / "calendar_UPDATED.csv").exists() and calendar == "calendar.csv" else (root / calendar)
    try:
        with cal_path.open(encoding="utf-8-sig", newline="") as handle:
            cal = list(csv.DictReader(handle))
    except UnicodeDecodeError:
        with cal_path.open(encoding="cp1252", newline="") as handle:
            cal = list(csv.DictReader(handle))
    canon = {}
    cpath = root / canonical
    if cpath.exists():
        with cpath.open(encoding="utf-8-sig", newline="") as handle:
            canon = {r["asset_id"]: r for r in csv.DictReader(handle)}
    out = []
    for row in cal:
        aid = row["asset_id"]
        files = []
        if aid in canon:
            first = root / canon[aid]["canonical_editable_source"]
            if first.suffix.lower() == ".html" and first.exists():
                files = sorted(first.parent.glob("*.html"))
        found = [scan_html(f) for f in files]
        fonts = sorted({x for f in found for x in f["fonts"]})
        urls = sorted({x for f in found for x in f["urls"]})
        imgs = sorted({x for f in found for x in f["images"]})
        is_video = row["format"] == "Short video"
        needs = ["rights evidence for every font, image, logo and third-party element named here"]
        if fonts:
            needs.append("font licence/terms for: " + ", ".join(fonts))
        if urls or imgs:
            needs.append("owner/licence for each external or image reference")
        if is_video:
            needs += [
                "source and licence of the voiceover/synthetic presenter (frames show AI presenter in IncuBrix hoodie with 4-point star watermark; exact external AI video generator UNCONFIRMED)",
                "source and licence of any audio/music track (AAC stream present per ffprobe)",
                "confirmation of IncuBrix logo/trademark permission and AI video generator commercial terms",
            ]
        visual_src = (
            "HTML/CSS authored in repo (rendered via content/designs/export-instagram.ps1 headless browser for IG; browser/html2canvas export for LI)"
            if not is_video
            else "Clean uncaptioned synthetic/AI presenter video in content/exports/youtube-shorts/ (4-point star watermark visible in frames; exact external generator name UNCONFIRMED; no burned-in subtitle overlay)"
        )
        out.append({
            "asset_id": aid, "platform": row["platform"],
            "scanned_files": len(files) if files else (0 if is_video else "none found"),
            "fonts_referenced": "; ".join(fonts) or ("none (clean uncaptioned video; no burned-in subtitle font)" if is_video else "none detected"),
            "external_urls": "; ".join(urls) or "none detected",
            "images_or_css_urls": "; ".join(imgs) or "none detected",
            "font_files_or_font_face": "yes" if any(f["font_face"] for f in found) else "no",
            "audio_video_refs": "yes" if any(f["av"] for f in found) else "no",
            "audio_track_in_final_file": "yes (AAC, per ffprobe)" if is_video else "n/a",
            "voice_source": "UNKNOWN - synthetic/AI presenter voice (candidate must document tool & terms)" if is_video else "n/a",
            "music_source": "UNKNOWN - candidate must confirm if background audio/music is present" if is_video else "n/a",
            "visual_source": visual_src,
            "rights_status": "PENDING HUMAN REVIEW",
            "ai_label_decision": (
                "REQUIRED (ai_label_needed=Yes) - realistic synthetic presenter/voice requires YouTube altered/synthetic content disclosure"
                if is_video
                else "PENDING - check platform AI-disclosure rule before publishing (ai_label_needed=Yes default in calendar.csv)"
            ),
            "required_evidence": " | ".join(needs)})
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="engine.rights_inventory")
    parser.add_argument("--root", default=".")
    parser.add_argument("--out", default="launch-kit/rights-inventory.csv")
    args = parser.parse_args(argv)
    try:
        rows = inventory(args.root)
    except (OSError, KeyError) as exc:
        print(f"ERROR: {exc}")
        return 1
    out = Path(args.root) / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} rows to {out}; all rights_status = PENDING HUMAN REVIEW")
    return 0


if __name__ == "__main__":
    sys.exit(main())
