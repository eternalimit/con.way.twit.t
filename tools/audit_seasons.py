#!/usr/bin/env python3
"""THE CUBE: read-only season parser, parity checker and evidence audit.

Run from the repo root: python3 tools/audit_seasons.py
Optional: python3 tools/audit_seasons.py --json
No external dependencies; does not write, publish, alter rights, or promote drafts.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOX = ROOT / "Conway_Twitty_Hollywood_Box_Set"
RIGHTS_RE = re.compile(r"(?:all rights reserved|copyright|©)", re.I)
HOLD_RE = re.compile(r"(?:0\s*·\s*HOLD|0\s+HOLD|0\s*→\s*∞\s*\+\s*1)", re.I)
CHAPTER_RE = re.compile(r"^#{2,4}\s+(\d{3})\s*[—–:\-]", re.M)
FILE_RE = re.compile(r"^EPISODE_(\d{3})_", re.I)
SEASON_NUM_RE = re.compile(r"^SEASON_(\d{3})\.md$", re.I)
SKIP = {"README.md", "HOOKS_AND_PRODUCTION.md", "SERIES_BIBLE.md"}

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def audit(root: Path) -> dict:
    box = root / "Conway_Twitty_Hollywood_Box_Set"
    findings = []
    entries = []
    episodes = {}
    def report(level, code, message, path=None):
        findings.append({"severity": level, "code": code, "message": message,
                         "path": str(path.relative_to(root)) if path else None})
    if not box.is_dir():
        report("ERROR", "BOX_SET_NOT_FOUND", "Box set directory is absent")
        return {"status": "FAIL", "seasons": [], "findings": findings}

    # Parse chapter IDs only from the actual episode-heading format.
    for path in sorted(box.glob("SEASON_???.md")):
        season = int(SEASON_NUM_RE.match(path.name).group(1))
        data = path.read_text(encoding="utf-8")
        ids = [int(i) for i in CHAPTER_RE.findall(data)]
        for i in ids:
            episodes.setdefault(i, []).append(str(path.relative_to(root)))
            if i // 100 != season:
                report("ERROR", "SEASON_NUMBER_MISMATCH", f"Episode {i} in Season {season:03d}", path)
        if not ids:
            report("WARN", "NO_PARSED_HEADINGS", "No 3-digit episode headings found", path)
        if not RIGHTS_RE.search(data):
            report("WARN", "RIGHTS_NOTICE_NOT_LOCAL", "Rights notice missing in this file; may exist in the collection README", path)
        entries.append({"season": f"{season:03d}", "source": str(path.relative_to(root)),
                        "type": "reconstructed development groupings", "episode_ids": ids,
                        "sha256": sha256(path), "release_verified": False})

    sneak = box / "SNEAK_PEEK_SEASON_003" / "SEASON_003_EPISODE_GUIDE.md"
    if sneak.is_file():
        data = sneak.read_text(encoding="utf-8")
        ids = sorted(set(int(x) for x in re.findall(r"(?<!\d)3(?:0\d|1\d|20)(?!\d)", data)))
        entries.append({"season": "003", "source": str(sneak.relative_to(root)),
                        "type": "development episode guide / proposed outline",
                        "episode_ids": ids, "sha256": sha256(sneak),
                        "release_verified": False})
        if len(ids) != 20:
            report("WARN", "SEASON_003_GUIDE_COUNT", f"Found {len(ids)} distinct 301–320 IDs; expected 20", sneak)
    else:
        report("WARN", "SEASON_003_GUIDE_MISSING", "Canonical sneak peek guide not found")

    # Physical screenplay files must remain separate from outlines.
    for path in sorted(box.glob("SEASON_???/EPISODE_*.md")) + sorted(box.glob("SNEAK_PEEK_SEASON_003/EPISODE_*.md")):
        match = FILE_RE.match(path.name)
        if not match:
            report("WARN", "UNPARSED_SCRIPT_NAME", "Unexpected episode filename", path)
            continue
        n = int(match.group(1))
        episodes.setdefault(n, []).append(str(path.relative_to(root)))
        data = path.read_text(encoding="utf-8")
        entries.append({"season": f"{n//100:03d}", "source": str(path.relative_to(root)),
                        "type": "screenplay draft / physical script file", "episode_ids": [n],
                        "sha256": sha256(path), "release_verified": False})
        if not RIGHTS_RE.search(data):
            report("WARN", "RIGHTS_NOTICE_NOT_LOCAL", "Script does not contain a rights notice", path)
        if not HOLD_RE.search(data):
            report("WARN", "HOLD_NOT_LOCAL", "Confirm 0 HOLD status manually", path)

    for n, sources in sorted(episodes.items()):
        # A grouping and a screenplay can have the same episode number legitimately.
        scripts = [s for s in sources if Path(s).name.startswith("EPISODE_")]
        if len(scripts) > 1:
            report("ERROR", "DUPLICATE_SCRIPT_ID", f"Episode {n} has multiple physical scripts: {scripts}")
    physical = sorted(i for i, s in episodes.items() if any(Path(x).name.startswith("EPISODE_") for x in s))
    s5 = [n for n in physical if n // 100 == 5]
    if s5:
        gaps = [n for n in range(min(s5), max(s5)+1) if n not in s5]
        if gaps:
            report("WARN", "SEASON_005_SEQUENCE_GAPS", f"Unverified gaps: {gaps}; not proof episodes are lost")
    if not entries:
        report("ERROR", "NO_SEASON_SOURCES", "No season material parsed")
    if not (root / "LICENSE").exists():
        report("ERROR", "LICENSE_MISSING", "Root LICENSE not found")
    status = "FAIL" if any(f["severity"] == "ERROR" for f in findings) else "PASS_WITH_WARNINGS" if findings else "PASS"
    return {"status": status, "mode": "read-only; 0 HOLD; no release authorization",
            "scope": str(box.relative_to(root)), "seasons": entries,
            "script_ids": physical, "findings": findings}

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = audit(args.root.resolve())
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("THE CUBE — PARSE / PARITY / EVIDENCE AUDIT:", result["status"])
        for e in result["seasons"]:
            print(f"  {e['season']} | {e['type']} | {e['episode_ids']} | {e['source']}")
        for f in result["findings"]:
            print(f"  {f['severity']} {f['code']}: {f['message']}")
        print("No finished film, complete verbatim season, licensing, or publication is inferred.")
    return 1 if result["status"] == "FAIL" else 0

if __name__ == "__main__":
    raise SystemExit(main())
