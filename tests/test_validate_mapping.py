import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(
    "plugins/cncr-plugin-marketplace/skills/cncr-page-process-create/scripts/validate_mapping.py"
)
SPEC = importlib.util.spec_from_file_location("validate_mapping", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


VALID_DOC = """## 1、接口定义
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
### 4.1 文案字块
| key | 中文文案 | 使用位置 |
|---|---|---|
| `page.title` | `查询结果演示` | `页头标题` |

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


REGION_UI_DOC = """## 1、接口定义
- QueryMiddlelayer

## 2、数据请求流程定义
<result-data-contract>
resultData.rows
resultData.headers
resultData.visibleFields
resultData.loading
resultData.errorMessage
</result-data-contract>

## 3、UI定义
### 区域1
- 区域名称：接入网占比
- 呈现方式：饼图
- 区域位置：
  - 横向：Left
  - 纵向：Top
- 查询来源：
  - 查询模式：QueryMiddlelayer
  - dataSetId：9999
  - tblId：8888
  - webModuleId：90066
- 查询字段：
  - requestDimensions：
    - rat
  - requestIndicators：
    - longitude
- 展示字段：
  - rat

### 区域2
- 区域名称：号码排行
- 呈现方式：柱状图
- 区域位置：
  - 横向：Center
  - 纵向：Top
- 查询来源：
  - 查询模式：QueryMiddlelayer
  - dataSetId：9999
  - tblId：8888
  - webModuleId：90066
- 查询字段：
  - requestDimensions：
    - msisdn
  - requestIndicators：
    - longitude
  - requestConditions：
    - rat=1|2|6
- 展示字段：
  - msisdn

## 4、全局状态与异常处理
### 4.1 加载状态
- 点击查询后进入 loading 状态。
- loading 结束后进入正常 / 空值 / 错误之一。

### 4.2 空值状态
- 查询成功但无数据时进入空值状态。
- 图表显示 empty，表格显示空态。

### 4.3 错误状态
- PREP 失败时进入错误状态。
- QUERY 失败时进入错误状态。
- 若出现 模块ID为空 / 无法获取权限信息 / 参数缺失，必须直接判定为失败。

## 5、文件结构
<scan-rule>
1. 先扫描复用
</scan-rule>
- src/view/query-dashboard/QueryDashboardGridPage.vue

## 6、注意事项
- 所有回填基于 resultData。
"""


class ValidateMappingTests(unittest.TestCase):
    def test_md_validation_is_business_driven_not_fixed_component_driven(self):
        result = MODULE.validate(VALID_DOC)

        self.assertTrue(result["valid"])
        self.assertEqual(result["matrix_rule_count"], 7)
        self.assertEqual(result["section_4_mode"], "fill-matrix")
        self.assertIn("networkPie", result["matrix_components_detected"])
        self.assertIn("headersToVisibleColumns", result["expected_transform_helpers"])
        self.assertTrue(result["expect_display_priority"])

    def test_md_validation_rejects_non_unified_source_field(self):
        invalid_doc = VALID_DOC.replace(
            "| `networkPie` | `series[0].data` | `resultData.rows` | `groupCountBy(ratTrans, fallback=rat)` | 接入网占比 |",
            "| `networkPie` | `series[0].data` | `rawResponse.rows` | `groupCountBy(ratTrans, fallback=rat)` | 接入网占比 |",
        )

        result = MODULE.validate(invalid_doc)

        self.assertFalse(result["valid"])
        self.assertTrue(any("未基于统一数据对象" in issue for issue in result["issues"]))

    def test_md_validation_accepts_region_based_middlequery_ui(self):
        result = MODULE.validate(REGION_UI_DOC)

        self.assertTrue(result["valid"])
        self.assertEqual(result["section_4_mode"], "global-state")
        self.assertEqual(result["ui_region_count"], 2)
        self.assertTrue(result["state_rules_detected"]["loading"])
        self.assertTrue(result["state_rules_detected"]["empty"])
        self.assertTrue(result["state_rules_detected"]["error"])
        self.assertEqual(result["ui_regions_detected"][0]["query_mode"], "QueryMiddlelayer")
        self.assertEqual(result["ui_regions_detected"][1]["horizontal_positions"], ["Center"])

    def test_md_validation_rejects_middlequery_region_missing_required_fields(self):
        invalid_doc = REGION_UI_DOC.replace("  - webModuleId：90066\n", "")

        result = MODULE.validate(invalid_doc)

        self.assertFalse(result["valid"])
        self.assertTrue(any("QueryMiddlelayer 缺少必填字段" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
