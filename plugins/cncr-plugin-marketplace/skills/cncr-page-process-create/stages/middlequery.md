# 阶段2.5：Middlequery 编排与区域查询合并

## 目标
- 读取业务执行 MD 中的“查询规则基线 + 区域查询定义”，负责真正的 QueryMiddlelayer 分组、PREP→QUERY 编排、区域复用判断与区域级回填验证。

## 文档依据（强制）
- 执行前必须参考以下资料：
  - 用户提供的业务执行 MD 第1节请求体样式示例
  - 用户提供的业务执行 MD 第3节 `UI定义`
  - `/Users/xuey/Desktop/查询接口说明(完整版) .docx`
  - `/Users/xuey/Desktop/cncr-workplace/packages/query-engine/AI_USAGE.md`
  - `/Users/xuey/Desktop/cncr-workplace/packages/query-engine/docs/queryMiddlelayer.md`
- 其中接口文档用于确认 PREP 参数能力边界；Skill 交付规则若比接口文档更收紧，以 Skill 规则为准。

## 第1章读取边界（强制）
- 第1章在业务执行 MD 中只保留以下内容：
  - 一个请求体样式示例（推荐保留 PREP）
  - 极少量协议基线（如加密 / 编码方式）
- 接口动作清单、字段含义表、PREP 参数组织、QUERY 分页换算、查询组拆分、是否复用、是否前端聚合，统一由本阶段负责，不得要求业务 MD 在第1章展开主流程细节。

## 接口动作清单（强制）
| 动作 | 地址 | 方法 | 作用 |
|---|---|---|---|
| PREP | `/brdcontrol-service/data/prep` | POST | 提交预处理请求，生成 `queryId` |
| QUERY | `/brdcontrol-service/data/query` | POST | 基于 `queryId` 查询结果数据 |
| STOP | `/brdcontrol-service/data/stop` | POST | 停止当前查询 |
| CANCEL | `/brdcontrol-service/data/cancel` | POST | 取消当前查询 |
| CLEAR | `/brdcontrol-service/data/clear` | POST | 清除当前查询会话 |
| EXPORT | `/brdcontrol-service/data/export` | POST | 发起导出任务 |
| EXPORT STATUS | `/brdcontrol-service/data/exportStatus` | GET | 查询导出任务状态 |
| STOP EXPORT | `/brdcontrol-service/data/stopExport` | POST | 停止当前导出任务 |
| EXPORT DOWN | `/brdcontrol-service/data/exportDown` | GET | 下载导出文件 |

## 核心字段含义表（强制）

### PREP 请求字段
| 字段 | 含义 | 是否必须 | 备注 |
|---|---|---|---|
| `dataSetId` | 数据集 ID | 是 | CNCR 交付中必填 |
| `tblId` | 数据表 ID | 是 | CNCR 交付中必填 |
| `webModuleId` | 应用模块 ID | 是 | CNCR 交付中必填 |
| `timeSize` | 时间粒度 | 否 | 如 `day` / `MONTH` |
| `requestDimensions` | 请求维度 | 否 | 决定查询粒度 |
| `requestIndicators` | 请求指标 | 否 | 指标字段或指标对象 |
| `requestConditions` | 请求条件 | 否 | 决定查询范围 |
| `requestSorts` | 排序字段 | 否 | 影响 TopN / 输出顺序 |
| `startPosi` | 开始条数 | 否 | legacy 场景可由引擎补齐 |
| `endPosi` | 结束条数 | 否 | legacy 场景可由引擎补齐 |
| `queryFirst` | 是否在 prep 后立刻查询 | 否 | 常由引擎控制 |
| `unuseCache` | 不使用缓存 | 否 | legacy 场景未传时通常补 `false` |

### QUERY 请求字段
| 字段 | 含义 | 是否必须 | 备注 |
|---|---|---|---|
| `queryId` | 查询会话 ID | 是 | 必须来自 PREP 响应 |
| `startPosi` | 开始行 | 是 | 由分页参数换算得到 |
| `endPosi` | 结束行 | 是 | 由分页参数换算得到 |

### 核心响应字段
| 字段 | 含义 | 用途 |
|---|---|---|
| `result` | 请求是否成功 | 判断成功 / 失败 |
| `msg` | 返回信息 | 错误提示与状态文案 |
| `queryId` | 查询 ID | 后续 QUERY / STOP / CANCEL / CLEAR / EXPORT 依赖 |
| `headers` | 表头描述 | 生成 `resultData.headers` |
| `datas` / `data` | 查询结果数据 | 生成 `resultData.rows` |
| `hasMoreData` | 是否还有更多数据 | 分页控制 |
| `total` / `totalCount` | 总记录数 | 分页与总量展示 |
| `exportKey` | 导出任务 key | 导出状态轮询与下载 |

## UI定义读取规则（强制）
- 第3节不再要求先定义“查询A / 查询B / 查询C”。
- 第3节的每个 `区域` 直接声明自己的查询需求，至少允许包含：
  - `区域名称`
  - `呈现方式`
  - `区域位置`（语义位置，如 `Left / Center / Right` + `Top / Middle / Bottom`）
  - `查询来源`
    - `查询模式`
    - `dataSetId`
    - `tblId`
    - `webModuleId`
  - `查询字段`
    - `requestDimensions`
    - `requestIndicators`
    - `requestConditions`
    - `requestSorts`
  - `展示字段`
- 禁止把运行态对象名（如 `resultData`）写成区域的“数据集”定义。区域里写的是查询来源，不是运行时回填对象。

## QueryMiddlelayer 专属收紧规则（强制）
- 仅当区域 `查询模式` 为 `QueryMiddlelayer` 或 `createBroadtechLegacyQueryMiddlelayer` 时，才进入本阶段的强校验。
- 对于 QueryMiddlelayer 区域，Skill 必须按 CNCR 交付约束收紧检查：
  - `dataSetId` 必填
  - `tblId` 必填
  - `webModuleId` 必填
- 即使接口文档中部分字段在服务端契约里标记为非强制，CNCR Skill 交付阶段仍按“三字段必填”验收。
- 任一字段为空时，必须输出：`Middlequery参数完整性: 失败FAIL`，并禁止输出“回填成功”或“实现无误”。

## 合并分组规则（强制）
- Skill 必须先遍历第3节全部区域，再决定查询分组，禁止边读边立即生成固定查询。
- QueryMiddlelayer 的默认合并策略必须采用**严格同签名**原则；只有满足以下条件的区域，才允许进入同一查询组：
  - `查询模式` 相同
  - `dataSetId` 相同
  - `tblId` 相同
  - `webModuleId` 相同
  - `timeSize` 相同或同为未声明
  - `requestDimensions` 完全相同
  - `requestIndicators` 完全相同
  - `requestConditions` 完全相同
  - `requestSorts` 完全相同
  - 分页策略不存在冲突
- 以下任一项不同，默认都必须拆分为独立查询组，不得为了“少查一次”强行合并：
  - `requestDimensions` 不同
  - `requestIndicators` 不同
  - `requestConditions` 不同
  - `requestSorts` 不同
  - `timeSize` 不同
  - 分页策略不同
- 原因说明（必须遵守）：
  - `requestDimensions` 决定查询粒度，通常对应不同的分组或明细结构，默认不可互相复用
  - `requestSorts` 直接影响 TopN / 排序结果集，不得视为“仅影响展示顺序”
  - `requestConditions` 直接改变查询范围，不得按“兼容”或“公共条件”强行合并

## 明细主查询复用特例（仅显式授权时允许）
- 只有当用户的业务执行 MD **明确声明**“允许使用明细主查询 + 前端聚合复用图表统计”时，才允许把多个区域合并到同一明细查询组。
- 即使业务执行 MD 显式允许，也必须同时满足以下条件：
  - 查询返回的是**足够完整的明细数据**，不是分页截断后的局部结果
  - 图表的统计口径允许在前端稳定聚合得到
  - TopN / 占比 / 排序逻辑允许在前端重算
  - 阶段输出中必须明确标注：`当前采用明细主查询 + 前端聚合复用，不是后端聚合查询复用`
- 若业务执行 MD 未明确授权该特例，则必须回到默认的严格同签名合并规则。

## PREP→QUERY 编排要求（强制）
- 每个查询组必须先 PREP，再 QUERY，禁止跳过 PREP 直接声称复用成功。
- 多个区域复用同一查询组时，必须明确输出：
  - 哪些区域归属同一查询组
  - 该查询组的 PREP 是否成功
  - 该查询组的 QUERY 是否成功
- 若判定为“不可合并”，必须明确输出拆组原因（如 `Dimensions不同`、`Sorts不同`、`Conditions不同`）。
- 若命中“明细主查询复用特例”，必须明确输出用户授权依据与前端聚合前提。

## 必须输出
- Middlequery 是否命中
- 区域→查询组映射
- 合并查询结果
- PREP→QUERY 编排结果
- Middlequery 参数完整性结论
- 区域级回填结论

## 推荐输出格式
- `Middlequery: 已命中 QueryMiddlelayer`
- `区域1 -> 查询组Q1`
- `区域2 -> 查询组Q1（复用）`
- `区域3 -> 查询组Q2`
- `区域1 与 区域2: 不合并（Dimensions不同）`
- `区域3 与 区域4: 不合并（Sorts不同）`
- `查询组Q1: PREP成功 / QUERY成功`
- `查询组Q2: PREP成功 / QUERY失败`
- `区域1: 成功OK`
- `区域2: 成功OK`
- `区域3: 失败FAIL（字段缺失）`

## 禁止事项
- 禁止把 QueryMiddlelayer 的区域分组逻辑继续混写回 `stages/api.md`。
- 禁止让业务执行 MD 先手工定义“查询A / 查询B”作为强依赖。
- 禁止把区域位置写成固定像素坐标要求；区域位置应优先使用语义定位。
- 禁止在区域定义中把 `resultData`、`canonical` 这类运行态对象误写成查询来源。
