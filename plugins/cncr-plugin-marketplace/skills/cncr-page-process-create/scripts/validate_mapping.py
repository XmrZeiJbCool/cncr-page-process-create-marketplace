#!/usr/bin/env python3
"""校验全流程页面开发模板的结构与映射约束。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REQUIRED_SECTIONS = [
    "## 1、接口定义",
    "## 2、数据请求流程定义",
    "## 3、UI定义",
    "## 4、字块填充定义",
    "## 5、文件机构",
    "## 6、注意事项",
]


def extract_section(text: str, heading: str) -> str:
    """按二级标题提取章节文本。"""
    pattern = re.compile(rf"{re.escape(heading)}[\\s\\S]*?(?=\\n##\\s\\d+、|\\Z)")
    match = pattern.search(text)
    return match.group(0) if match else ""


def find_missing_sections(text: str) -> list[str]:
    return [s for s in REQUIRED_SECTIONS if s not in text]


def validate(text: str) -> dict:
    issues: list[str] = []

    missing_sections = find_missing_sections(text)
    if missing_sections:
        issues.append("缺少章节: " + ", ".join(missing_sections))

    if "<canonical-contract>" not in text and "canonical-contract" not in text:
        issues.append("第2节缺少 canonical contract 定义")

    if "scan-rule" not in text:
        issues.append("第5节缺少 scan-rule 规则")

    if "src/view" not in text:
        issues.append("第5节缺少 src/view 文件落盘约束")

    if "UI回填" not in text and "回填矩阵" not in text:
        issues.append("第4节缺少 UI回填定义")

    canonical_refs = re.findall(r"canonical\.[A-Za-z0-9_\[\]\.]+", text)
    if not canonical_refs:
        issues.append("第4节未检测到 canonical.* 回填字段")

    section_ui = extract_section(text, "## 3、UI定义")
    if section_ui and (
        "<ui-grid-schema>" in section_ui
        or re.search(r"<row\\s|<col\\s|widget=|gutter=", section_ui)
    ):
        issues.append("第3节应为业务大白话，不应直接写 ui-grid-schema（由 Skill 自动转换）")

    if re.search(r"datas\[\]\.name|datas\[\]\.value", text) and "canonical." not in text:
        issues.append("检测到直接使用原始字段，缺少 canonical 映射隔离")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "canonical_refs_detected": sorted(set(canonical_refs)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="校验全流程页面开发模板")
    parser.add_argument("--md", required=True, help="模板文件路径")
    args = parser.parse_args()

    md_path = Path(args.md).expanduser().resolve()
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    result = validate(text)
    print(json.dumps({"file": str(md_path), **result}, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
