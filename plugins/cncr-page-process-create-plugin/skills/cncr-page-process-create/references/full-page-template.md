# 全流程页面开发模板（固定版）

> 规则：1/2可切换，3/4/5/6固定。

## 0、技能前置检查

- 执行前必须检查是否存在 `~/.claude/skills/full-page-dev/SKILL.md`。
- 若存在：继续执行第1~6节。
- 若不存在：提示安装 full-page-dev skills，安装完成后再执行第1~6节。

<skill-check>
  <required name="full-page-dev" path="~/.claude/skills/full-page-dev/SKILL.md" />
  <on-missing>
    <step>提示：未检测到 full-page-dev skills</step>
    <step>建议安装：远端仓库安装或本地包安装</step>
    <step>安装完成后重新加载会话并重读本文件</step>
  </on-missing>
</skill-check>

## 1、接口定义【可切换】

- 写清：baseURL、method、path、请求包装字段。
- 写清：必填字段（例如 dataSetId、webModuleId、queryId 等）。

<endpoint-base>
  <env name="local" baseURL="http://127.0.0.1:8000" />
  <env name="dev" baseURL="${VITE_API_BASE_URL}" />
  <rule>最终URL = baseURL + path</rule>
</endpoint-base>

## 2、数据请求流程定义【可切换】

- PREP → QUERY（可含 CHECK）
- 把原始字段映射为统一契约字段（见 canonical-contract）

<canonical-contract>
  <field name="queryId" type="string" required="true" />
  <field name="chartData" type="array<{name:string,value:number}>" required="true" />
  <field name="loading" type="boolean" required="true" />
  <field name="errorMessage" type="string" required="false" />
</canonical-contract>

## 3、UI定义【固定】

- 只写业务布局大白话（例如：第一行饼图/柱图/饼图，第二行柱图/饼图/柱图，第三行整行表格）。
- 标题区
- 查询按钮区（默认仅按钮）
- 状态区（loading/empty/error）
- 图表/表格区（ECharts + Table）
- 栅格技术细节（Row/Col/span/断点）由 Skill 自动转换，不要求写在实施MD。

## 4、字块填充定义【固定核心】

- 文案字块表（key → 文案 → 使用位置）
- UI回填矩阵（组件目标位 ← canonical字段 ← 转换规则）

| componentId | targetPath | sourceField | transform |
|---|---|---|---|
| chartA | series[0].data | canonical.chartData | identity |
| chartA | legend.data | canonical.chartData[].name | pluckName |

<hard-rule>
UI层禁止直接读取原始接口字段，只允许读取 canonical 字段。
</hard-rule>

## 5、文件机构（文件存放规则）【固定】

<scan-rule>
实现前必须自动扫描可复用 API/组件；有复用则禁止重复新建。
</scan-rule>

- 页面：`src/view/...`
- API：优先复用；确无复用时新建 `src/api/...`

## 6、注意事项【固定】

- 敏感信息不可出现在日志。
- 必须覆盖成功/空数据/失败三态。
- 验收前必须完成字段映射校验 + 回填校验 + 构建校验。
