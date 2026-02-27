#!/usr/bin/env python3
"""扫描项目中的可复用 API/组件候选。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

API_DIRS = ("src/api", "src/service")
COMPONENT_DIRS = ("src/components",)

API_KEYWORDS = ("prep", "query", "check", "page", "cancel", "stop", "request", "api")
COMP_KEYWORDS = ("chart", "echarts", "card", "button", "state", "empty", "error")

TEXT_EXTS = {".ts", ".tsx", ".js", ".jsx", ".vue", ".py", ".md"}


def iter_files(base: Path, rel_dirs: Iterable[str]) -> Iterable[Path]:
    for rel in rel_dirs:
        d = base / rel
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if p.is_file() and p.suffix.lower() in TEXT_EXTS:
                yield p


def score_file(path: Path, keywords: tuple[str, ...]) -> int:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        return 0
    return sum(1 for kw in keywords if kw in text)


def top_candidates(files: Iterable[Path], keywords: tuple[str, ...], top_n: int = 8) -> list[dict]:
    scored = []
    for f in files:
        score = score_file(f, keywords)
        if score > 0:
            scored.append((score, f))
    scored.sort(key=lambda x: (-x[0], str(x[1])))
    return [{"path": str(f), "score": s} for s, f in scored[:top_n]]


def main() -> int:
    parser = argparse.ArgumentParser(description="扫描 API/组件复用候选")
    parser.add_argument("--root", required=True, help="项目根目录")
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    api_files = list(iter_files(root, API_DIRS))
    comp_files = list(iter_files(root, COMPONENT_DIRS))

    view_dir = root / "src/view"
    if view_dir.exists():
        comp_files.extend([p for p in view_dir.rglob("*.vue") if p.is_file()])

    api_hits = top_candidates(api_files, API_KEYWORDS)
    comp_hits = top_candidates(comp_files, COMP_KEYWORDS)

    result = {
        "root": str(root),
        "api_candidates": api_hits,
        "component_candidates": comp_hits,
        "decision": {
            "reuse_api": len(api_hits) > 0,
            "reuse_component": len(comp_hits) > 0,
            "create_api_under": "src/api" if len(api_hits) == 0 else "reuse-existing",
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
