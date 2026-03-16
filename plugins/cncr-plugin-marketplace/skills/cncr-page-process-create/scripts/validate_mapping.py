#!/usr/bin/env python3
"""校验执行 MD 与生成代码的通用回填约束。"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

SECTION_4_ALIASES = ["## 4、字块填充定义", "## 4、文案与回填定义", "## 4、全局状态与异常处理"]
REQUIRED_MATRIX_COLUMNS = {"componentId", "targetPath", "sourceField", "transform"}
REQUIRED_SECTION_ALIASES = [
    ["## 1、接口定义", "## 1、查询规则", "## 1、请求体样式"],
    ["## 2、数据请求流程定义"],
    ["## 3、UI定义"],
    SECTION_4_ALIASES,
    ["## 5、文件机构", "## 5、文件结构", "## 5、目录规范"],
    ["## 6、注意事项"],
]
CODE_EXTENSIONS = {".vue", ".ts", ".tsx", ".js", ".jsx"}
IGNORED_DIR_NAMES = {
    ".git",
    ".helloagents",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
}
GENERIC_RESULTDATA_FIELDS = ["rows", "headers", "visibleFields", "loading", "errorMessage"]
RAW_RESPONSE_PATTERNS = [
    r"\brawResponse\b",
    r"\b(?:response|res)\s*\.\s*data\b",
    r"\bdatas\s*\[",
]

QUERY_MIDDLELAYER_TOKENS = ["QueryMiddlelayer", "createBroadtechLegacyQueryMiddlelayer"]
QUERY_MIDDLELAYER_REQUIRED_FIELDS = ["dataSetId", "tblId", "webModuleId"]
QUERY_MIDDLELAYER_ERROR_TOKENS = ["模块ID为空", "无法获取权限信息", "权限不足", "参数缺失"]
TRANSFORM_RESERVED_WORDS = {"fallback", "identity", "resultData", "canonical"}
UI_RUNTIME_OBJECT_TOKENS = {"resultData", "canonical"}
SEMANTIC_HORIZONTAL_TOKENS = {"Left", "Center", "Right"}
SEMANTIC_VERTICAL_TOKENS = {"Top", "Middle", "Bottom"}


def extract_section(text: str, heading: str) -> str:
    """Return the content of a level-2 section by exact heading.

    Args:
        text: Full Markdown text.
        heading: Exact section heading.

    Returns:
        Section text or an empty string.
    """
    pattern = re.compile(rf"{re.escape(heading)}[\s\S]*?(?=\n##\s\d+、|\Z)")
    match = pattern.search(text)
    return match.group(0) if match else ""



def extract_section_by_aliases(text: str, headings: list[str]) -> str:
    """Return the first matched section text from multiple aliases."""
    for heading in headings:
        section = extract_section(text, heading)
        if section:
            return section
    return ""



def normalize_cell(value: str) -> str:
    """Normalize a Markdown table cell value."""
    return value.strip().strip("`").strip()



def is_delimiter_cell(value: str) -> bool:
    """Check whether a table cell is a Markdown delimiter cell."""
    compact = value.replace(" ", "")
    return bool(compact) and all(char in "-:" for char in compact)



def parse_markdown_tables(section_text: str) -> list[dict[str, object]]:
    """Extract Markdown tables from a section.

    Args:
        section_text: Section text.

    Returns:
        Parsed tables with headers and rows.
    """
    tables: list[dict[str, object]] = []
    lines = section_text.splitlines()
    index = 0
    while index < len(lines) - 1:
        header_line = lines[index].strip()
        divider_line = lines[index + 1].strip()
        if not (header_line.startswith("|") and divider_line.startswith("|")):
            index += 1
            continue
        headers = [normalize_cell(cell) for cell in header_line.strip("|").split("|")]
        divider = [normalize_cell(cell) for cell in divider_line.strip("|").split("|")]
        if len(headers) != len(divider) or not all(is_delimiter_cell(cell) for cell in divider):
            index += 1
            continue
        row_index = index + 2
        rows: list[dict[str, str]] = []
        while row_index < len(lines):
            row_line = lines[row_index].strip()
            if not row_line.startswith("|"):
                break
            cells = [normalize_cell(cell) for cell in row_line.strip("|").split("|")]
            if len(cells) != len(headers):
                break
            rows.append(dict(zip(headers, cells)))
            row_index += 1
        tables.append({"headers": headers, "rows": rows})
        index = row_index
    return tables



def find_fill_matrix_table(section_text: str) -> dict[str, object] | None:
    """Locate the fill matrix table inside section 4."""
    for table in parse_markdown_tables(section_text):
        headers = set(table["headers"])
        if REQUIRED_MATRIX_COLUMNS.issubset(headers):
            return table
    return None



def find_missing_sections(text: str) -> list[str]:
    """Find required missing sections in the execution MD."""
    missing: list[str] = []
    for aliases in REQUIRED_SECTION_ALIASES:
        if not any(alias in text for alias in aliases):
            missing.append(" / ".join(aliases))
    return missing



def parse_transform_name(transform: str) -> str:
    """Extract the helper name from a transform expression."""
    match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)", transform)
    return match.group(1) if match else ""



def extract_transform_tokens(transform: str) -> list[str]:
    """Extract business tokens referenced by a transform expression."""
    raw_tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", transform)
    helper_name = parse_transform_name(transform)
    tokens: list[str] = []
    for token in raw_tokens:
        if token == helper_name or token in TRANSFORM_RESERVED_WORDS:
            continue
        if token.isupper():
            continue
        tokens.append(token)
    return sorted(set(tokens))



def build_rule_key(component_id: str, target_path: str) -> str:
    """Build a stable rule key."""
    return f"{component_id}->{target_path}"



def classify_rule_domain(rule: dict[str, str]) -> str:
    """Infer the UI domain for a fill rule."""
    target = rule["targetPath"].lower()
    component = rule["componentId"].lower()
    if target in {"columns", "datasource"} or "table" in component:
        return "table"
    if target in {"loading", "errortext", "exportkey"} or "state" in component:
        return "state"
    return "chart"


def extract_ui_regions(section_text: str) -> list[dict[str, object]]:
    """Extract region blocks from section 3 UI definition."""
    matches = list(re.finditer(r"^###\s+([^\n]+)", section_text, flags=re.MULTILINE))
    regions: list[dict[str, object]] = []
    for index, match in enumerate(matches):
        start_offset = match.start()
        end_offset = matches[index + 1].start() if index + 1 < len(matches) else len(section_text)
        block = section_text[start_offset:end_offset].strip()
        title = match.group(1).strip()
        for marker in ("\n**交互与合并查询约束**", "\n<hard-rule>"):
            marker_index = block.find(marker)
            if marker_index != -1:
                block = block[:marker_index].strip()
        query_mode_match = re.search(r"查询模式\s*[:：]\s*([^\n]+)", block)
        data_set_match = re.search(r"dataSetId\s*[:：]\s*([^\n]+)", block)
        tbl_match = re.search(r"tblId\s*[:：]\s*([^\n]+)", block)
        module_match = re.search(r"webModuleId\s*[:：]\s*([^\n]+)", block)
        horizontal_values = set(re.findall(r"\b(Left|Center|Right)\b", block))
        vertical_values = set(re.findall(r"\b(Top|Middle|Bottom)\b", block))
        regions.append(
            {
                "title": title,
                "block": block,
                "query_mode": query_mode_match.group(1).strip() if query_mode_match else "",
                "dataSetId": data_set_match.group(1).strip() if data_set_match else "",
                "tblId": tbl_match.group(1).strip() if tbl_match else "",
                "webModuleId": module_match.group(1).strip() if module_match else "",
                "has_request_dimensions": "requestDimensions" in block,
                "has_request_indicators": "requestIndicators" in block,
                "has_request_conditions": "requestConditions" in block,
                "has_request_sorts": "requestSorts" in block,
                "horizontal_positions": sorted(horizontal_values),
                "vertical_positions": sorted(vertical_values),
                "uses_runtime_object_as_source": any(
                    re.search(rf"[：:]\s*{token}\b", block) for token in UI_RUNTIME_OBJECT_TOKENS
                ),
            }
        )
    return regions



def validate_ui_regions(section_text: str) -> tuple[list[dict[str, object]], list[str]]:
    """Validate region-based UI definition for middlequery scenarios."""
    issues: list[str] = []
    regions = extract_ui_regions(section_text)
    for region in regions:
        title = str(region["title"])
        query_mode = str(region["query_mode"])
        if region["uses_runtime_object_as_source"]:
            issues.append(f"{title} 把运行态对象写成查询来源（如 resultData/canonical），应改写查询来源字段")
        if query_mode and query_mode in QUERY_MIDDLELAYER_TOKENS:
            missing_fields = [
                field
                for field in QUERY_MIDDLELAYER_REQUIRED_FIELDS
                if not str(region[field]).strip()
            ]
            if missing_fields:
                issues.append(f"{title} 的 QueryMiddlelayer 缺少必填字段: {', '.join(missing_fields)}")
            if not (
                region["has_request_dimensions"]
                or region["has_request_indicators"]
                or region["has_request_conditions"]
                or region["has_request_sorts"]
            ):
                issues.append(f"{title} 缺少 QueryMiddlelayer 查询字段定义")
        if (region["horizontal_positions"] or region["vertical_positions"]) and not (
            region["horizontal_positions"] and region["vertical_positions"]
        ):
            issues.append(f"{title} 的区域位置需同时声明横向与纵向语义定位")
    return regions, issues


def validate_global_state_section(section_text: str) -> tuple[dict[str, bool], list[str]]:
    """Validate the simplified global-state section for v0.3.1."""
    issues: list[str] = []
    state_rules = {
        "loading": "加载状态" in section_text and any(token in section_text for token in ("loading", "加载中", "加载态")),
        "empty": "空值状态" in section_text and any(token in section_text for token in ("empty", "空态", "暂无数据", "暂无可视化数据")),
        "error": "错误状态" in section_text and any(token in section_text for token in ("error", "失败", "错误", "权限不足", "参数缺失")),
    }
    if not state_rules["loading"]:
        issues.append("第4.1节缺少 加载状态 定义")
    if not state_rules["empty"]:
        issues.append("第4.2节缺少 空值状态 定义")
    if not state_rules["error"]:
        issues.append("第4.3节缺少 错误状态 定义")
    return state_rules, issues


def validate(text: str) -> dict:
    """Validate the execution MD itself.

    Args:
        text: Markdown content.

    Returns:
        Validation result and parsed fill matrix summary.
    """
    issues: list[str] = []

    missing_sections = find_missing_sections(text)
    if missing_sections:
        issues.append("缺少章节: " + ", ".join(missing_sections))

    has_contract = any(token in text for token in ("canonical-contract", "result-data-contract"))
    if not has_contract:
        issues.append("第2节缺少统一数据契约定义（canonical-contract 或 result-data-contract）")

    if "scan-rule" not in text:
        issues.append("第5节缺少 scan-rule 规则")
    if "src/view" not in text:
        issues.append("第5节缺少 src/view 文件落盘约束")

    canonical_refs = re.findall(r"canonical\.[A-Za-z0-9_\[\]\.]+", text)
    result_data_refs = re.findall(r"resultData\.[A-Za-z0-9_\[\]\.]+", text)
    unified_refs = sorted(set(canonical_refs + result_data_refs))

    section_ui = extract_section(text, "## 3、UI定义")
    ui_regions: list[dict[str, object]] = []
    if section_ui and ("<ui-grid-schema>" in section_ui or re.search(r"<row\s|<col\s|widget=|gutter=", section_ui)):
        issues.append("第3节应保持业务表达，禁止把技术栅格细节直接写进执行 MD")
    if section_ui:
        ui_regions, ui_region_issues = validate_ui_regions(section_ui)
        issues.extend(ui_region_issues)

    section_4 = extract_section_by_aliases(text, SECTION_4_ALIASES)
    matrix_rule_count = 0
    matrix_components_detected: list[str] = []
    matrix_rule_keys: list[str] = []
    parsed_fill_rules: list[dict[str, str]] = []
    expected_transform_helpers: list[str] = []
    section_4_mode = "unknown"
    state_rules_detected = {"loading": False, "empty": False, "error": False}

    if not section_4:
        issues.append("缺少第4节正文")
    else:
        matrix_table = find_fill_matrix_table(section_4)
        if matrix_table:
            section_4_mode = "fill-matrix"
            rows: list[dict[str, str]] = matrix_table["rows"]  # type: ignore[assignment]
            matrix_rule_count = len(rows)
            parsed_fill_rules = rows
            matrix_components_detected = sorted({row["componentId"] for row in rows})
            matrix_rule_keys = [build_rule_key(row["componentId"], row["targetPath"]) for row in rows]
            invalid_sources = []
            for row in rows:
                source_field = row["sourceField"]
                if not (source_field.startswith("resultData.") or source_field.startswith("canonical.")):
                    invalid_sources.append(f"{build_rule_key(row['componentId'], row['targetPath'])}({source_field})")
            if invalid_sources:
                issues.append("第4.2节以下回填规则未基于统一数据对象: " + ", ".join(invalid_sources))
            expected_transform_helpers = sorted(
                {
                    helper_name
                    for helper_name in (parse_transform_name(row["transform"]) for row in rows)
                    if helper_name and helper_name != "identity"
                }
            )
            if not unified_refs:
                issues.append("第4节未检测到统一结果对象回填字段（canonical.* 或 resultData.*）")
        else:
            section_4_mode = "global-state"
            state_rules_detected, state_issues = validate_global_state_section(section_4)
            issues.extend(state_issues)

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "unified_refs_detected": unified_refs,
        "canonical_refs_detected": sorted(set(canonical_refs)),
        "result_data_refs_detected": sorted(set(result_data_refs)),
        "matrix_rule_count": matrix_rule_count,
        "matrix_components_detected": matrix_components_detected,
        "matrix_rule_keys": matrix_rule_keys,
        "parsed_fill_rules": parsed_fill_rules,
        "expected_transform_helpers": expected_transform_helpers,
        "section_4_mode": section_4_mode,
        "state_rules_detected": state_rules_detected,
        "expect_display_priority": "headers[].display" in text,
        "expect_rat_trans_priority": "ratTrans" in text and "rat" in text,
        "expect_numeric_conversion": any(token in text for token in ("latitude", "longitude", "数值转换", "数值型")),
        "ui_region_count": len(ui_regions),
        "ui_regions_detected": [
            {
                "title": region["title"],
                "query_mode": region["query_mode"],
                "dataSetId": region["dataSetId"],
                "tblId": region["tblId"],
                "webModuleId": region["webModuleId"],
                "horizontal_positions": region["horizontal_positions"],
                "vertical_positions": region["vertical_positions"],
            }
            for region in ui_regions
        ],
    }



def should_ignore_path(path: Path) -> bool:
    """Return whether a path should be ignored during code scanning."""
    return any(part in IGNORED_DIR_NAMES for part in path.parts)



def find_code_files(root_path: Path) -> list[Path]:
    """Collect source files under the code root."""
    files: list[Path] = []
    for path in root_path.rglob("*"):
        if should_ignore_path(path):
            continue
        if path.is_file() and path.suffix in CODE_EXTENSIONS:
            files.append(path)
    return sorted(files)



def read_code_files(root_path: Path) -> dict[str, str]:
    """Read scanned code files into a relative-path mapping."""
    file_map: dict[str, str] = {}
    for path in find_code_files(root_path):
        file_map[str(path.relative_to(root_path))] = path.read_text(encoding="utf-8", errors="ignore")
    return file_map



def join_texts(file_map: dict[str, str], selected_paths: list[str] | None = None) -> str:
    """Join file contents for aggregate searching."""
    if selected_paths is None:
        return "\n".join(file_map.values())
    return "\n".join(file_map[path] for path in selected_paths)



def filter_paths(file_map: dict[str, str], keywords: tuple[str, ...]) -> list[str]:
    """Filter files by lowercase path keywords."""
    result: list[str] = []
    for relative_path in file_map:
        lowered = relative_path.lower()
        if any(keyword in lowered for keyword in keywords):
            result.append(relative_path)
    return sorted(result)



def detect_resultdata_access(text: str, field_name: str) -> bool:
    """Detect whether code defines or consumes a resultData field."""
    patterns = [
        rf"resultData\.{re.escape(field_name)}\b",
        rf"\{{[^}}]*\b{re.escape(field_name)}\b[^}}]*\}}\s*=\s*resultData\b",
        rf"\b{re.escape(field_name)}\b\s*:\s*resultData\.{re.escape(field_name)}\b",
        rf"resultData\s*:\s*\{{[\s\S]{{0,4000}}?\b{re.escape(field_name)}\b",
    ]
    return any(re.search(pattern, text) for pattern in patterns)



def detect_display_priority(text: str) -> bool:
    """Detect a clear display-first fallback implementation."""
    patterns = [
        r"title\s*:\s*[^\n\r]*display[^\n\r]*(?:\|\||\?\?|\?)",
        r"display[^\n\r]*(?:rawName|raw_name|name|field|key|title)",
    ]
    return all(re.search(pattern, text) for pattern in patterns)



def detect_rat_trans_priority(text: str) -> bool:
    """Detect ratTrans-first fallback to rat."""
    return bool(re.search(r"ratTrans[^\n\r]*(?:\|\||\?\?|\?)\s*[^\n\r]*rat", text))



def detect_coordinate_conversion(text: str) -> bool:
    """Detect explicit latitude/longitude numeric conversion."""
    patterns = [
        r"latitude\s*:\s*(?:Number|parseFloat)\(",
        r"longitude\s*:\s*(?:Number|parseFloat)\(",
    ]
    return all(re.search(pattern, text) for pattern in patterns)



def find_suspicious_raw_usage(file_map: dict[str, str]) -> list[str]:
    """Detect suspicious raw-response usage outside normalization files."""
    findings: list[str] = []
    for relative_path, text in file_map.items():
        lowered = relative_path.lower()
        if any(keyword in lowered for keyword in ("queryflow", "flow", "service", "api")):
            continue
        for pattern in RAW_RESPONSE_PATTERNS:
            if re.search(pattern, text):
                findings.append(f"{relative_path}: {pattern}")
    return findings



def uses_query_middlelayer(text: str) -> bool:
    """Return whether code uses QueryMiddlelayer-based request implementation."""
    return any(token in text for token in QUERY_MIDDLELAYER_TOKENS)



def detect_query_middlelayer_required_fields(text: str) -> list[str]:
    """Return missing required request fields for QueryMiddlelayer code paths."""
    return [field_name for field_name in QUERY_MIDDLELAYER_REQUIRED_FIELDS if field_name not in text]



def detect_query_middlelayer_error_tokens(text: str) -> list[str]:
    """Return permission or missing-parameter error tokens found in code or output handling."""
    return [token for token in QUERY_MIDDLELAYER_ERROR_TOKENS if token in text]


def build_area_status(area_name: str, component_id: str, passed: bool, message: str, files: list[str]) -> dict[str, object]:
    """Build a single area-level validation record."""
    return {
        "area": area_name,
        "componentId": component_id,
        "status": "OK" if passed else "FAIL",
        "message": message,
        "files": files,
    }



def format_area_summary(area_status: list[dict[str, object]]) -> list[str]:
    """Format area-level statuses as human-readable summary lines."""
    lines: list[str] = []
    for item in area_status:
        result_text = "成功OK" if item["status"] == "OK" else "失败FAIL"
        lines.append(f"{item['area']}: {result_text}（{item['message']}）")
    return lines



def derive_area_labels(rules: list[dict[str, str]]) -> dict[str, str]:
    """Derive human-readable area labels from business-driven rules."""
    counters = defaultdict(int)
    labels: dict[str, str] = {}
    ordered_components: list[str] = []
    domains_by_component: dict[str, str] = {}
    for rule in rules:
        component_id = rule["componentId"]
        if component_id in domains_by_component:
            continue
        domains_by_component[component_id] = classify_rule_domain(rule)
        ordered_components.append(component_id)
    for component_id in ordered_components:
        domain = domains_by_component[component_id]
        counters[domain] += 1
        prefix = {"chart": "图表", "table": "表格", "state": "状态区"}[domain]
        labels[component_id] = f"{prefix}{counters[domain]}"
    return labels



def build_generic_area_status(file_map: dict[str, str], chart_files: list[str], table_files: list[str], view_files: list[str]) -> list[dict[str, object]]:
    """Build fallback area statuses when no business MD is provided."""
    area_status: list[dict[str, object]] = []
    if chart_files:
        for index, relative_path in enumerate(chart_files, start=1):
            text = file_map[relative_path]
            passed = "resultData" in text and "rows" in text
            message = "检测到图表回填文件" if passed else "缺少 resultData.rows 消费"
            area_status.append(build_area_status(f"图表{index}", relative_path, passed, message, [relative_path]))
    else:
        area_status.append(build_area_status("图表1", "", False, "未检测到图表回填代码", []))

    if table_files:
        for index, relative_path in enumerate(table_files, start=1):
            text = file_map[relative_path]
            passed = all(token in text for token in ("resultData", "headers", "rows"))
            message = "检测到表格回填文件" if passed else "缺少 headers/rows 消费"
            area_status.append(build_area_status(f"表格{index}", relative_path, passed, message, [relative_path]))
    else:
        area_status.append(build_area_status("表格1", "", False, "未检测到表格回填代码", []))

    if view_files:
        for index, relative_path in enumerate(view_files, start=1):
            text = file_map[relative_path]
            passed = any(token in text for token in ("loading", "errorMessage"))
            message = "检测到页面状态回填文件" if passed else "缺少状态字段消费"
            area_status.append(build_area_status(f"状态区{index}", relative_path, passed, message, [relative_path]))
    else:
        area_status.append(build_area_status("状态区1", "", False, "未检测到页面状态回填代码", []))
    return area_status



def validate_component_rules(
    component_id: str,
    rules: list[dict[str, str]],
    area_label: str,
    chart_text: str,
    table_text: str,
    state_text: str,
    normalization_text: str,
    md_flags: dict[str, bool],
) -> tuple[bool, str]:
    """Validate a business component against code evidence."""
    domain = classify_rule_domain(rules[0])
    domain_text = {"chart": chart_text, "table": table_text, "state": state_text}[domain]
    failures: list[str] = []

    for rule in rules:
        source_tail = rule["sourceField"].split(".")[-1]
        helper_name = parse_transform_name(rule["transform"])
        tokens = [token for token in extract_transform_tokens(rule["transform"]) if token != source_tail]

        if source_tail and not detect_resultdata_access(domain_text + "\n" + normalization_text, source_tail):
            failures.append(f"缺少 {source_tail} 消费")
        if helper_name and helper_name != "identity" and helper_name not in domain_text:
            failures.append(f"缺少 helper: {helper_name}")
        missing_tokens = [token for token in tokens if token not in domain_text and token not in normalization_text]
        if missing_tokens:
            failures.append(f"缺少规则字段: {', '.join(missing_tokens)}")

    if domain == "table":
        if md_flags.get("expect_display_priority") and not detect_display_priority(table_text):
            failures.append("缺少 headers[].display 优先回退")
    if domain == "chart":
        if md_flags.get("expect_rat_trans_priority") and not detect_rat_trans_priority(chart_text + "\n" + normalization_text):
            failures.append("缺少 ratTrans 优先展示")
        if md_flags.get("expect_numeric_conversion") and any(token in chart_text for token in ("longitude", "latitude")):
            if not detect_coordinate_conversion(normalization_text):
                failures.append("缺少经纬度数值转换")
    if domain == "state":
        for token in ("loading", "errorMessage"):
            if token in {rule["targetPath"] for rule in rules} and token not in state_text:
                failures.append(f"缺少 {token} 状态绑定")

    if failures:
        return False, "；".join(sorted(set(failures)))
    return True, "回填规则与代码实现证据一致"



def validate_code_root(root_path: Path, md_text: str | None = None) -> dict:
    """Validate generated code, optionally against a business execution MD.

    Args:
        root_path: Root path of generated code.
        md_text: Optional execution MD content.

    Returns:
        Combined static validation result.
    """
    issues: list[str] = []
    file_map = read_code_files(root_path)
    if not file_map:
        empty_area_status = [
            build_area_status("图表1", "", False, "未检测到图表回填代码", []),
            build_area_status("表格1", "", False, "未检测到表格回填代码", []),
            build_area_status("状态区1", "", False, "未检测到页面状态回填代码", []),
        ]
        return {
            "valid": False,
            "issues": ["未在代码目录中扫描到可分析的前端源码文件"],
            "files_scanned": [],
            "result_data_fields_detected": [],
            "result_data_refs_detected": [],
            "business_fields_detected": [],
            "normalization_files": [],
            "chart_files": [],
            "table_files": [],
            "view_files": [],
            "suspicious_raw_usages": [],
            "missing_helpers": [],
            "area_fill_status": empty_area_status,
            "area_fill_summary": format_area_summary(empty_area_status),
        }

    all_text = join_texts(file_map)
    normalization_files = filter_paths(file_map, ("queryflow", "flow", "service", "api"))
    chart_files = filter_paths(file_map, ("chart", "option"))
    table_files = filter_paths(file_map, ("table",))
    view_files = [path for path in file_map if path.endswith(".vue")]
    normalization_text = join_texts(file_map, normalization_files) if normalization_files else all_text
    chart_text = join_texts(file_map, chart_files) if chart_files else all_text
    table_text = join_texts(file_map, table_files) if table_files else all_text
    state_text = join_texts(file_map, view_files) if view_files else all_text

    if not normalization_files:
        issues.append("未检测到归一化/查询流程文件（建议至少包含 queryFlow/flow/service/api 之一）")

    result_data_fields_detected = [field for field in GENERIC_RESULTDATA_FIELDS if detect_resultdata_access(all_text, field)]
    missing_resultdata_fields = [field for field in GENERIC_RESULTDATA_FIELDS if field not in result_data_fields_detected]
    if missing_resultdata_fields:
        issues.append("代码中缺少 resultData 关键字段定义或消费: " + ", ".join(missing_resultdata_fields))

    suspicious_raw_usages = find_suspicious_raw_usage(file_map)
    if suspicious_raw_usages:
        issues.append("检测到可疑的原始响应直连（非归一化层）: " + "; ".join(suspicious_raw_usages))

    query_middlelayer_detected = uses_query_middlelayer(all_text)
    missing_query_middlelayer_fields: list[str] = []
    query_middlelayer_error_tokens: list[str] = []
    if query_middlelayer_detected:
        missing_query_middlelayer_fields = detect_query_middlelayer_required_fields(all_text)
        query_middlelayer_error_tokens = detect_query_middlelayer_error_tokens(all_text)
        if missing_query_middlelayer_fields:
            issues.append(
                "QueryMiddlelayer 缺少必填字段: " + ", ".join(missing_query_middlelayer_fields)
            )
        if query_middlelayer_error_tokens:
            issues.append(
                "QueryMiddlelayer 命中风险错误信号: " + ", ".join(query_middlelayer_error_tokens)
            )

    md_validation: dict | None = None
    missing_helpers: list[str] = []
    area_fill_status: list[dict[str, object]] = []
    business_fields_detected: list[str] = []

    if md_text is not None:
        md_validation = validate(md_text)
        if md_validation["issues"]:
            issues.extend([f"业务MD: {issue}" for issue in md_validation["issues"]])
        parsed_fill_rules: list[dict[str, str]] = md_validation["parsed_fill_rules"]
        expected_helpers: list[str] = md_validation["expected_transform_helpers"]
        missing_helpers = [helper for helper in expected_helpers if helper not in all_text]
        if missing_helpers:
            issues.append("代码中缺少业务MD要求的 transform helper: " + ", ".join(missing_helpers))

        business_fields_detected = sorted(
            {
                token
                for rule in parsed_fill_rules
                for token in extract_transform_tokens(rule["transform"])
                if token in all_text and token not in {"resultData", "canonical"}
            }
        )
        area_labels = derive_area_labels(parsed_fill_rules)
        rules_by_component: dict[str, list[dict[str, str]]] = defaultdict(list)
        for rule in parsed_fill_rules:
            rules_by_component[rule["componentId"]].append(rule)
        flags = {
            "expect_display_priority": md_validation["expect_display_priority"],
            "expect_rat_trans_priority": md_validation["expect_rat_trans_priority"],
            "expect_numeric_conversion": md_validation["expect_numeric_conversion"],
        }
        for component_id, rules in rules_by_component.items():
            passed, message = validate_component_rules(
                component_id=component_id,
                rules=rules,
                area_label=area_labels[component_id],
                chart_text=chart_text,
                table_text=table_text,
                state_text=state_text,
                normalization_text=normalization_text,
                md_flags=flags,
            )
            if not passed:
                issues.append(f"{component_id}: {message}")
            relevant_files = {
                "chart": chart_files,
                "table": table_files,
                "state": view_files,
            }[classify_rule_domain(rules[0])]
            area_fill_status.append(
                build_area_status(area_labels[component_id], component_id, passed, message, relevant_files)
            )
    else:
        business_fields_detected = sorted(
            {token for token in ("endtime", "imsi", "msisdn", "tacid", "longitude", "latitude", "ratTrans", "rat") if token in all_text}
        )
        area_fill_status = build_generic_area_status(file_map, chart_files, table_files, view_files)

    result_data_refs = sorted(set(re.findall(r"resultData\.[A-Za-z0-9_\[\]\.]+", all_text)))

    return {
        "valid": len(issues) == 0,
        "issues": sorted(set(issues)),
        "files_scanned": sorted(file_map.keys()),
        "result_data_fields_detected": result_data_fields_detected,
        "result_data_refs_detected": result_data_refs,
        "business_fields_detected": business_fields_detected,
        "normalization_files": normalization_files,
        "chart_files": chart_files,
        "table_files": table_files,
        "view_files": view_files,
        "suspicious_raw_usages": suspicious_raw_usages,
        "query_middlelayer_detected": query_middlelayer_detected,
        "missing_query_middlelayer_fields": missing_query_middlelayer_fields,
        "query_middlelayer_error_tokens": query_middlelayer_error_tokens,
        "missing_helpers": missing_helpers,
        "area_fill_status": area_fill_status,
        "area_fill_summary": format_area_summary(area_fill_status),
        "md_validation": md_validation,
    }



def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="校验执行MD或生成代码的通用回填约束")
    parser.add_argument("--md", help="执行MD文件路径")
    parser.add_argument("--code-root", help="生成代码根目录")
    args = parser.parse_args()

    if not args.md and not args.code_root:
        parser.error("至少需要传入 --md 或 --code-root")

    md_text = None
    md_path = None
    if args.md:
        md_path = Path(args.md).expanduser().resolve()
        md_text = md_path.read_text(encoding="utf-8", errors="ignore")

    if args.code_root:
        code_root = Path(args.code_root).expanduser().resolve()
        result = validate_code_root(code_root, md_text=md_text)
        payload = {"mode": "code", "code_root": str(code_root), **result}
        if md_path is not None:
            payload["md_file"] = str(md_path)
    else:
        result = validate(md_text or "")
        payload = {"mode": "md", "file": str(md_path), **result}

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["valid"] else 1)


if __name__ == "__main__":
    main()
