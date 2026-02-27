# 全流程页面开发执行文档

目标：交给 Claude Code 执行，落地一个可扩展页面；本次实例为 **3×3 栅格**：
- 第1行：饼图 / 柱状图 / 饼图
- 第2行：柱状图 / 饼图 / 柱状图
- 第3行：表格（整行）

范围：本文件仅用于规范执行，不直接写代码。

<hard-rule>
本文件是唯一执行规范。必须严格按 1~6 节执行；未声明字段、未声明流程、未声明文件不得擅自新增。
</hard-rule>

---

## 0、技能前置检查

- 执行前必须检查插件 `cncr-plugin-marketplace@cncr-marketplace` 是否已安装并启用。
- 若已安装且启用：继续执行第1~6节。
- 若未安装：先自动安装，再提示用户 `/new` 后重试。

<skill-check>
  <required plugin="cncr-plugin-marketplace@cncr-marketplace" command="claude plugin list" />
  <on-missing>
    <step>执行：`claude plugin install cncr-plugin-marketplace@cncr-marketplace`</step>
    <step>执行：`claude plugin enable cncr-plugin-marketplace@cncr-marketplace`</step>
    <step>输出：已安装skills，请执行 /new 后重试。</step>
    <step>停止当前流程，不继续第1~6节。</step>
  </on-missing>
</skill-check>

<hard-rule>
未检测到插件时必须先执行安装；安装后必须提示“已安装skills，请执行 /new 后重试。”并停止本次流程。
</hard-rule>

---

<hard-rule>
1. 接口/字段/映射必须严格来自本 MD；未声明内容禁止自动补充。
2. 未输出 skill-proof 前，禁止进入扫描与开发。
3. 默认禁止自行创建 mock（例如 mock_server.py）；仅可复用已有 mock。
4. 仅当本 MD 明确要求创建 mock 且用户确认后，才允许新增 mock。
</hard-rule>

## 1、接口定义

### 1.1 接口地址配置

<endpoint-base>
  <env name="local-mock" baseURL="http://127.0.0.1:8000" />
  <env name="dev" baseURL="${VITE_API_BASE_URL}" />
  <rule>最终URL = baseURL + path</rule>
</endpoint-base>

- 本地联调默认：`http://127.0.0.1:8000`
- 组件内禁止硬编码完整 URL，必须由配置组装。

### 1.2 接口清单
| 接口名 | 地址 | 方法 | Content-Type | 请求体 |
|---|---|---|---|---|
| 查询预处理 | `/brdcontrol-service/data/prep` | POST | `application/json` | `{"prepParam":"<AES密文>"}` |
| 图表查询 | `/brdcontrol-service/data/query` | POST | `application/json` | `{"queryParam":"<AES密文>"}` |
| 表格查询 | `/brdcontrol-service/data/query` | POST | `application/json` | `{"queryParam":"<AES密文>"}` |
| 检查查询信息（可选） | `/brdcontrol-service/data/check` | POST | `application/json` | `{"queryId":"<queryId>"}` |

### 1.3 PREP 明文参数模板
```json
{
  "dataSetId": 10050000069,
  "tblId": "10050000058",
  "tableTblId": "10050000059",
  "dataSourceId": "cfg_user_nps",
  "webModuleName": "用户推荐分析",
  "webModuleId": "10050000077",
  "moduleFrom": 1,
  "page": 1,
  "queryId": "",
  "drillIndex": "",
  "timeSize": "MONTH",
  "directQuerySQL": null,
  "directSQLDataSource": "IMPALA",
  "directSQLEncrypt": false,
  "xdrSql": false,
  "exportQuery": false,
  "requestIndicators": [
    {"name": "kpi_recom_users", "nameCn": "推荐用户数"},
    {"name": "kpi_active_users", "nameCn": "活跃用户数"},
    {"name": "kpi_lost_users", "nameCn": "流失用户数"}
  ],
  "requestDimensions": [
    {"id": "city_trans"}
  ],
  "requestConditions": [],
  "requestSorts": [],
  "translateFields": [],
  "startPosi": 1,
  "endPosi": 500,
  "queryFirst": false,
  "unuseCache": false
}
```

- PREP 实际请求体：
```json
{
  "prepParam": "<PREP明文JSON经 AES/ECB/PKCS5Padding + Base64 后的密文>"
}
```

### 1.4 QUERY 明文参数模板
```json
{
  "queryId": "<prep返回queryId>",
  "dataSetId": 10050000069,
  "tblId": "10050000058",
  "startPosi": 1,
  "endPosi": 500
}
```

- QUERY 实际请求体：
```json
{
  "queryParam": "<QUERY明文JSON经 AES/ECB/PKCS5Padding + Base64 后的密文>"
}
```

### 1.5 QUERY 表格参数模板
```json
{
  "queryId": "<prep返回queryId>",
  "dataSetId": 10050000069,
  "tblId": "10050000059",
  "page": 1,
  "size": 20
}
```

- QUERY 实际请求体：
```json
{
  "queryParam": "<QUERY表格参数明文JSON经 AES/ECB/PKCS5Padding + Base64 后的密文>"
}
```

### 1.6 关键响应字段

#### 图表查询关键字段
| 字段 | 类型 | 说明 |
|---|---|---|
| `result` | boolean | 请求是否成功 |
| `msg` | string | 返回信息 |
| `queryId` | string | 查询ID |
| `datas` | array | 图表数据源（目标结构 `[{name,value}]`） |

#### 表格查询关键字段
| 字段 | 类型 | 说明 |
|---|---|---|
| `result` | boolean | 请求是否成功 |
| `msg` | string | 返回信息 |
| `headers` | array | 表头描述（name/display） |
| `data` | array[] | 表格二维数组数据 |

<hard-rule>
1. `dataSetId`、`webModuleId` 必填；`tblId` 本次必须传。
2. `queryId` 必须来自 PREP 返回，不得伪造。
3. 图表与表格均调用 `/data/query`，通过 `dataSetId + tblId` 区分后端数据表。
4. PREP 与 QUERY 默认走 AES 包装。
</hard-rule>

---

## 2、数据请求流程定义

### 2.1 默认流程
- 第一步：点击“开始查询”触发 PREP。
- 第二步：从 PREP 响应提取 `queryId`。
- 第三步：并行/串行调用：
  - 图表查询 `/data/query`（传图表 `tblId`）
  - 表格查询 `/data/query`（传表格 `tblId`）
- 第四步：把图表与表格响应共同转换到标准契约（canonical）。
- 第五步：按第4节回填矩阵，回填 6 图 + 1 表。

### 2.2 标准数据契约
<canonical-contract>
  <field name="queryId" type="string" required="true" />
  <field name="pieData" type="array<{name:string,value:number}>" required="true" />
  <field name="barCategories" type="array<string>" required="true" />
  <field name="barValues" type="array<number>" required="true" />
  <field name="tableColumns" type="array<{key:string,title:string,dataIndex:string}>" required="true" />
  <field name="tableRows" type="array<object>" required="true" />
  <field name="loading" type="boolean" required="true" />
  <field name="errorMessage" type="string" required="false" />
</canonical-contract>

### 2.3 映射与转换规则
| 来源 | 源字段路径 | 目标契约字段 | 转换规则 |
|---|---|---|---|
| PREP响应 | `$.queryId` | `canonical.queryId` | 直接映射 |
| QUERY响应（图表tblId） | `$.datas` | `canonical.pieData` | `normalizeNameValue` |
| QUERY响应（图表tblId） | `$.datas[].name` | `canonical.barCategories` | `pluckName` |
| QUERY响应（图表tblId） | `$.datas[].value` | `canonical.barValues` | `toNumberList` |
| QUERY响应（表格tblId） | `$.headers` | `canonical.tableColumns` | `headersToColumns` |
| QUERY响应（表格tblId） | `$.data` | `canonical.tableRows` | `matrixToRowObjects` |
| 任一失败 | `$.msg` 或异常 | `canonical.errorMessage` | 文案透传 |

### 2.4 本地联调示例
- PREP：`POST http://127.0.0.1:8000/brdcontrol-service/data/prep`
- QUERY（图表tblId）：`POST http://127.0.0.1:8000/brdcontrol-service/data/query`
- QUERY（表格tblId）：`POST http://127.0.0.1:8000/brdcontrol-service/data/query`

<hard-rule>
1. UI层只读 canonical，不允许直接读取原始接口字段。
2. 图表与表格都必须先映射到 canonical 再回填。
3. 流程失败必须进入错误态回填，不得静默失败。
</hard-rule>

---

## 3、UI定义

### 3.1 页面布局描述
- 页面分三行。
- 第一行：饼图 / 柱状图 / 饼图。
- 第二行：柱状图 / 饼图 / 柱状图。
- 第三行：整行表格。
- 小屏按单列换行；中大屏按三列展示；卡片间距建议 16 或 24。

### 3.2 组件槽位定义
| widgetId | 布局位 | 组件类型 | 说明 |
|---|---|---|---|
| `pieA` | 第一行左侧 | Pie | 饼图 |
| `barA` | 第一行中间 | Bar | 柱状图 |
| `pieB` | 第一行右侧 | Pie | 饼图 |
| `barB` | 第二行左侧 | Bar | 柱状图 |
| `pieC` | 第二行中间 | Pie | 饼图 |
| `barC` | 第二行右侧 | Bar | 柱状图 |
| `tableMain` | 第三行整行 | Table | 表格（整行） |

### 3.3 页面交互
- 点击“开始查询”后：
  - 进入 loading
  - 执行 PREP→QUERY(图表tblId)+QUERY(表格tblId)
  - 成功：按第4节回填矩阵回填到全部 widget
  - 空数据：显示 empty
  - 失败：显示 error

<hard-rule>
1. 第3节只写业务布局，不写 `Row/Col/span/breakpoint` 等技术细节。
2. 栅格技术化转换由 Skill 执行，输出标准 `ui-grid-schema`。
3. 最终实现必须满足“上两行图表、下行表格”的结构。
</hard-rule>

---

## 4、字块填充定义

### 4.1 文案字块
| key | 中文文案 | 使用位置 |
|---|---|---|
| `page.title` | 图表表格联动栅格演示 | 页头标题 |
| `page.btn.query` | 开始查询 | 查询按钮 |
| `state.loading` | 数据加载中... | loading态 |
| `state.empty` | 暂无数据 | empty态 |
| `state.error` | 查询失败，请重试 | error态 |
| `widget.pieA.title` | 饼图A | pieA标题 |
| `widget.barA.title` | 柱图A | barA标题 |
| `widget.pieB.title` | 饼图B | pieB标题 |
| `widget.barB.title` | 柱图B | barB标题 |
| `widget.pieC.title` | 饼图C | pieC标题 |
| `widget.barC.title` | 柱图C | barC标题 |
| `widget.table.title` | 数据表 | table标题 |

### 4.2 UI回填矩阵
| componentId | targetPath | sourceField | transform | 说明 |
|---|---|---|---|---|
| `pieA` | `series[0].data` | `canonical.pieData` | `identity` | 饼图数据 |
| `pieB` | `series[0].data` | `canonical.pieData` | `sortByValueAsc` | 饼图排序变体 |
| `pieC` | `series[0].data` | `canonical.pieData` | `top5ByValueDesc` | 饼图Top5 |
| `barA` | `xAxis.data` | `canonical.barCategories` | `identity` | 柱图类目 |
| `barA` | `series[0].data` | `canonical.barValues` | `identity` | 柱图数值 |
| `barB` | `xAxis.data` | `canonical.barCategories` | `identity` | 柱图类目 |
| `barB` | `series[0].data` | `canonical.barValues` | `sortDesc` | 柱图排序 |
| `barC` | `xAxis.data` | `canonical.barCategories` | `identity` | 柱图类目 |
| `barC` | `series[0].data` | `canonical.barValues` | `top5` | 柱图Top5 |
| `tableMain` | `columns` | `canonical.tableColumns` | `identity` | 表头回填 |
| `tableMain` | `dataSource` | `canonical.tableRows` | `identity` | 表格行回填 |
| `globalState` | `loading` | `canonical.loading` | `identity` | 状态回填 |
| `globalState` | `errorText` | `canonical.errorMessage` | `identity` | 错误态回填 |

<hard-rule>
1. 第4节必须同时覆盖：文案回填 + 图表回填 + 表格回填 + 状态回填。
2. 回填来源必须是 canonical 字段，禁止直接写原始响应字段到组件。
</hard-rule>

---

## 5、文件机构

> 要求：页面代码在 `src/view`；接口请求先扫描复用，复用不到再落到 `src/api`。

### 5.1 执行前扫描规则
<scan-rule>
在创建/修改文件前，必须先执行：
1. 扫描 `src/api/`、`src/service/` 是否已有 prep/query 类请求封装。
2. 扫描 `src/components/`、`src/view/**/components/` 是否有可复用图表/表格组件。
3. 若存在可复用项，必须优先复用并记录复用来源路径。
4. 若不存在可复用 API，才允许新建 `src/api/query.ts`（同一路径 query，按 `dataSetId + tblId` 组装请求）。
</scan-rule>

### 5.2 文件落盘规则
| 文件路径 | 职责 | 操作类型 |
|---|---|---|
| `src/view/query-dashboard/QueryDashboardGridPage.vue` | 3×3页面布局与交互 | 新增 |
| `src/view/query-dashboard/queryFlow.ts` | PREP→QUERY(图表tblId)+QUERY(表格tblId) 流程与契约转换 | 新增 |
| `src/view/query-dashboard/chartOptions.ts` | 饼图/柱图 option 组装 | 新增 |
| `src/view/query-dashboard/tableAdapter.ts` | QUERY表格tblId响应转 columns/dataSource | 新增 |
| `src/view/query-dashboard/copy.ts` | 字块定义 | 新增 |
| `src/view/query-dashboard/types.ts` | 类型定义 | 新增 |
| `src/api/query.ts` | PREP/QUERY 请求封装（query按 `dataSetId + tblId` 区分图表与表格） | 条件新增 |

<hard-rule>
1. 页面主逻辑文件必须落在 `src/view/query-dashboard/`。
2. API请求文件不得先建后扫；必须先执行 scan-rule。
</hard-rule>

---

## 6、注意事项

- 默认禁止新建 mock 服务文件；仅在文档明确要求且用户确认后才允许创建。
- AES规则：`AES/ECB/PKCS5Padding`，key=`broadtechbdvkey1`，UTF-8，Base64。
- 日志禁止输出完整密钥、完整密文、敏感凭据。
- 本次 UI 不做参数输入框，仅按钮触发。
- 必须覆盖三态：成功 / 空数据 / 错误。
- FastAPI mock 需模拟请求延迟：约 `3s`（用于验证 loading 态）。

<hard-rule>
交付前必须通过：
- 构建通过
- 第4节回填矩阵逐项实现并可追踪
- “上两行图表 + 下行表格”栅格布局正确渲染
- mock延迟生效且 loading 态可见
</hard-rule>

---

## 验收清单
- [ ] PREP / QUERY 地址、字段、包装方式正确
- [ ] 点击按钮后可完成 PREP→双QUERY（图表tblId+表格tblId）链路
- [ ] 已构建 canonical，并回填 6 图 + 1 表
- [ ] 布局满足 3×3（上两行图表、下行表格）
- [ ] 成功/空数据/失败 三态可验证
- [ ] mock延迟约3秒可观察
- [ ] 文件落盘符合第5节规则
