import importlib.util
import tempfile
import textwrap
import unittest
from pathlib import Path


SCRIPT_PATH = Path(
    "plugins/cncr-plugin-marketplace/skills/cncr-page-process-create/scripts/validate_mapping.py"
)
SPEC = importlib.util.spec_from_file_location("validate_mapping", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


BUSINESS_MD = """## 1、接口定义
- ok

## 2、数据请求流程定义
<result-data-contract>
resultData.rows
resultData.headers
resultData.visibleFields
resultData.loading
resultData.errorMessage
</result-data-contract>

## 3、UI定义
- 顶部图表区域 + 下方表格区域

## 4、文案与回填定义
### 4.2 UI回填矩阵
| componentId | targetPath | sourceField | transform | 说明 |
|---|---|---|---|---|
| `networkPie` | `series[0].data` | `resultData.rows` | `groupCountBy(ratTrans, fallback=rat)` | 接入网占比 |
| `timeBar` | `xAxis.data` | `resultData.rows` | `groupCountCategoriesBy(endtime)` | 时间类目 |
| `timeBar` | `series[0].data` | `resultData.rows` | `groupCountValuesBy(endtime)` | 时间值 |
| `recordsTable` | `columns` | `resultData.headers` | `headersToVisibleColumns(resultData.visibleFields)` | 列定义 |
| `recordsTable` | `dataSource` | `resultData.rows` | `filterRowsByVisibleFields(resultData.visibleFields)` | 行数据 |
| `pageState` | `loading` | `resultData.loading` | `identity` | 加载态 |
| `pageState` | `errorText` | `resultData.errorMessage` | `identity` | 错误态 |

<hard-rule>
1. 表格列头必须优先使用 headers[].display。
2. 图表展示若存在 ratTrans，必须优先使用 ratTrans，回退 rat。
3. latitude/longitude 必须在 resultData 阶段完成数值转换后再参与绘制。
</hard-rule>

## 5、文件结构
<scan-rule>
1. 先扫描复用
</scan-rule>
- src/view/query-dashboard/QueryDashboardGridPage.vue

## 6、注意事项
- 所有回填基于 resultData。
"""


def write_file(root: Path, relative_path: str, content: str) -> None:
    target = root / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(textwrap.dedent(content).strip() + "\n", encoding="utf-8")


class ValidateGeneratedCodeTests(unittest.TestCase):
    def test_code_validation_uses_business_md_as_source_of_truth(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_file(
                root,
                "src/view/query-dashboard/queryFlow.ts",
                """
                export function normalizeHeaderMeta(header) {
                  return {
                    key: (header.name || header.rawName || '').toLowerCase(),
                    title: header.display || header.name || header.rawName || '',
                  };
                }
                export function matrixToRowObjectsByHeaders(headers, data) {
                  return data.map((matrixRow) => {
                    const row = {};
                    headers.map((header, index) => {
                      const normalized = normalizeHeaderMeta(header);
                      row[normalized.key] = matrixRow[index];
                      return normalized;
                    });
                    return {
                      ...row,
                      latitude: Number(row.latitude),
                      longitude: Number(row.longitude),
                      ratTrans: row.ratTrans || row.rat,
                    };
                  });
                }
                export function createResultData(response) {
                  const rows = matrixToRowObjectsByHeaders(response.headers, response.data);
                  return {
                    resultData: {
                      rows,
                      headers: response.headers.map(normalizeHeaderMeta),
                      visibleFields: ['endtime', 'imsi', 'msisdn', 'ratTrans', 'longitude'],
                      loading: false,
                      errorMessage: '',
                    },
                  };
                }
                """,
            )
            write_file(
                root,
                "src/view/query-dashboard/chartOptions.ts",
                """
                export function groupCountBy(rows, fieldName, fallbackField) {
                  return [rows, fieldName, fallbackField];
                }
                export function groupCountCategoriesBy(rows, fieldName) {
                  return [rows, fieldName];
                }
                export function groupCountValuesBy(rows, fieldName) {
                  return [rows, fieldName];
                }
                export function buildChartOptions(resultData) {
                  const { rows } = resultData;
                  return {
                    networkPie: groupCountBy(rows, 'ratTrans', 'rat'),
                    timeBar: {
                      categories: groupCountCategoriesBy(rows, 'endtime'),
                      values: groupCountValuesBy(rows, 'endtime'),
                    },
                  };
                }
                """,
            )
            write_file(
                root,
                "src/view/query-dashboard/tableAdapter.ts",
                """
                export function headersToVisibleColumns(headers, visibleFields) {
                  return visibleFields.map((field) => {
                    const header = headers.find((item) => item.key === field || item.name === field || item.rawName === field) || {};
                    return {
                      key: field,
                      title: header.display || header.title || header.rawName || header.name || field,
                    };
                  });
                }
                export function filterRowsByVisibleFields(rows, visibleFields) {
                  return rows.map((row) => Object.fromEntries(visibleFields.map((field) => [field, row[field]])));
                }
                export function createTableState(resultData) {
                  const { headers, visibleFields, rows } = resultData;
                  return {
                    columns: headersToVisibleColumns(headers, visibleFields),
                    dataSource: filterRowsByVisibleFields(rows, visibleFields),
                  };
                }
                """,
            )
            write_file(
                root,
                "src/view/query-dashboard/QueryDashboardGridPage.vue",
                """
                <script setup lang="ts">
                const props = defineProps({ resultData: { type: Object, required: true } });
                const loading = props.resultData.loading;
                const errorMessage = props.resultData.errorMessage;
                </script>
                """,
            )

            result = MODULE.validate_code_root(root, md_text=BUSINESS_MD)

            self.assertTrue(result["valid"])
            self.assertEqual(result["missing_helpers"], [])
            self.assertTrue(any(item.startswith("图表1: 成功OK") for item in result["area_fill_summary"]))
            self.assertTrue(any(item.startswith("表格1: 成功OK") for item in result["area_fill_summary"]))
            self.assertTrue(any(area["componentId"] == "recordsTable" and area["status"] == "OK" for area in result["area_fill_status"]))

    def test_code_validation_fails_when_business_md_required_helpers_are_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_file(
                root,
                "src/view/query-dashboard/queryFlow.ts",
                """
                export function createResultData(response) {
                  return {
                    resultData: {
                      rows: response.data,
                      headers: response.headers,
                      visibleFields: [],
                      loading: false,
                      errorMessage: '',
                    },
                  };
                }
                """,
            )
            write_file(
                root,
                "src/view/query-dashboard/chartOptions.ts",
                """
                export function createOverviewOptions(resultData) {
                  return resultData.rows;
                }
                """,
            )
            write_file(
                root,
                "src/view/query-dashboard/tableAdapter.ts",
                """
                export function createTableState(resultData) {
                  return { columns: [], dataSource: resultData.rows };
                }
                """,
            )

            result = MODULE.validate_code_root(root, md_text=BUSINESS_MD)

            self.assertFalse(result["valid"])
            self.assertTrue(any("transform helper" in issue for issue in result["issues"]))
            self.assertTrue(any(item.endswith("失败FAIL（缺少 helper: groupCountBy") or "失败FAIL" in item for item in result["area_fill_summary"]))

    def test_query_middlelayer_requires_three_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_file(
                root,
                "src/view/query-dashboard/queryFlow.ts",
                """
                import { createBroadtechLegacyQueryMiddlelayer } from '@cncr/query-engine';
                export function createFlow() {
                  return createBroadtechLegacyQueryMiddlelayer({ dataSetId: 'A', tblId: 'B' });
                }
                """,
            )
            write_file(
                root,
                "src/view/query-dashboard/QueryDashboardGridPage.vue",
                """
                <script setup lang="ts">
                const loading = false;
                const errorMessage = '';
                </script>
                """,
            )

            result = MODULE.validate_code_root(root, md_text=BUSINESS_MD)

            self.assertFalse(result["valid"])
            self.assertTrue(result["query_middlelayer_detected"])
            self.assertIn("webModuleId", result["missing_query_middlelayer_fields"])
            self.assertTrue(any("QueryMiddlelayer 缺少必填字段" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
