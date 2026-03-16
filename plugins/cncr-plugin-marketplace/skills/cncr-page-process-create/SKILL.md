---
name: cncr-page-process-create
description: 使用用户提供的业务执行 MD 推进同类 UI 开发；功能 Skill 负责流程、预检闸门、阶段输出与校验框架，业务范式由执行 MD 驱动
---

# cncr-page-process-create

用于“业务执行 MD 驱动的同类 UI 开发流程”。

## 核心定位（强制）

- 本 Skill 是**功能 Skill**，负责流程控制、预检闸门、阶段约束、输出规范、校验框架。
- 业务范式（页面布局、区块数量、组件命名、字段映射、回填矩阵）必须来自用户提供的业务执行 MD。
- 禁止把 `6 图 + 1 表`、`pieA/barA/tableMain` 等固定业务范式写死进功能 Skill。

## 输出前缀规则（强制）

- 本技能执行过程中，所有对用户可见的回复都必须以 `【CNCR_SKILLS】` 开头。

## 交互模式约束（强制）

- 禁止进入 `Plan mode`、`update_plan`、TODO 面板或其他计划展示模式。
- 禁止调用 `askuserquerytion`、`askuserquestion`、`request_user_input` 等交互式提问工具。
- 默认采用直接执行；确实缺失阻断信息时，只允许一次性普通文本说明缺失项。

## 执行文档来源约束（强制）

- 本技能只认用户明确提供的业务执行 MD。
- 禁止回退到任何默认模板或示例文档作为主执行依据。
- 用户执行 MD 与其他参考资料冲突时，以用户执行 MD 为唯一执行规范。

## 固定启动快照（强制）

读取业务执行 MD 后，必须先按以下固定编号原样输出，且不得省略标题：
1. 项目目录
2. 代理情况
3. 私包安装状态
4. 设计预览模式（1 使用 pencli MCP / 2 不使用）

## 执行流程（按阶段加载）

1. 读取业务执行 MD
2. 输出固定启动快照
3. 按顺序加载并执行以下阶段文件：
   - `stages/preflight.md`
   - `stages/scan.md`
   - `stages/api.md`
   - `stages/middlequery.md`
   - `stages/result-data.md`
   - `stages/fill.md`
   - `stages/style-validate.md`
   - `stages/runtime-validate.md`
   - `stages/frontend-smoke.md`
   - `stages/delivery.md`
4. 每个阶段必须按对应阶段文件中的“必须输出”部分回报结果。
5. 未完成当前阶段前，不得跳到下一阶段。

## 业务执行 MD 章节作用（参考）

- 第1章：只保留一个请求体样式示例（推荐保留 PREP 请求体），用于告诉 Skill“这一类请求对象长什么样”；不在本章展开接口动作、字段说明与主流程。
- 第2章：定义统一数据契约、字段映射、类型转换与数据流转图输出要求。
- 第3章：定义业务区域、查询来源、展示字段与语义位置；这是 `stages/middlequery.md` 的主要输入。
- 第4章：定义全局 `loading / empty / error` 状态与错误处理边界；由回填与运行时验证阶段消费。
- 第5章：定义目录规范与落盘约束，只说明“主页面、局部组件、工具类、API、共享组件”各自应该放在哪里，不写死具体文件名清单。
- 第6章：定义实现注意事项、验收补充约束与最终交付边界。

## 通用强规则

- 禁止在 UI 层直接读取原始接口字段，必须经过统一结果对象。
- 禁止先新建文件后扫描复用，必须先扫后建。
- 复用扫描必须遵循：项目内 → 私仓 → 新建实现。
- `@cncr/query-engine` 是默认优先的请求实现来源，不应被当作普通可选依赖跳过。
- 若任务涉及 `@cncr/query-engine`，必须优先读取 `/Users/xuey/Desktop/cncr-workplace/packages/query-engine/AI_USAGE.md`，并按其中顺序继续读取 `README.md`、`docs/INDEX.md`、`docs/queryMiddlelayer.md` 后再决定复用或改造方式。
- 未明确决定弃用 `@cncr/query-engine` 前，禁止默认新建一套独立请求层；若最终未使用，必须在交付说明中写明原因。
- 页面代码落在 `src/view/...`；接口请求复用优先，确无复用才落 `src/api/...`。
- 默认走真实接口；若业务 MD 未明确要求 mock，禁止擅自新增 mock。
- 若用户要求“查看验证结果/打印验证结果”，默认解释为必须同时输出运行时验证结果与静态校验结果，而不只是口头说明。
- 样式还原必须单独验收，不得用“功能已跑通”替代“视觉已对齐”。
- 预开发阶段必须先让用户选择设计预览模式：`1 使用 pencli MCP` / `2 不使用设计预览`。
- 用户选择 `1` 时，默认优先使用 pencli MCP 生成设计预览图；只有在 pencli MCP 不可用时，才允许退回 Mermaid 结构图。
- 用户选择 `2` 时，必须明确记录“设计预览已跳过（用户选择）”，随后直接进入扫描/实现阶段，不得强行补做 pencli 设计。
- 设计预览阶段必须优先加载兄弟 Skill `cncr-design-aesthetic`，并按其规则生成预览；除非业务执行 MD 明确指定了不同视觉要求。
- 设计预览绘制前必须先确认画布尺寸；若业务执行 MD 未指定，默认使用 `1920x1080` 桌面画布，并按该画布完整展开布局。
- 使用 pencli MCP 生成设计预览时，默认必须先自动执行“新建空白设计文档”动作，再在该空白文档中承载预览；禁止清空当前画布，禁止默认复用已有设计稿。
- 一旦用户基于 pencli 设计预览回复 `继续开发`，后续实现必须以该设计预览为直接参考；不得擅自改动布局结构、组件层级和主要视觉方向。
- 若请求实现走 `QueryMiddlelayer` / `createBroadtechLegacyQueryMiddlelayer`，API 验收阶段必须检查 `dataSetId`、`tblId`、`webModuleId` 非空。
- 无论用户是否使用设计预览，预检阶段都必须输出标准流程图结构的数据流转图，不得只写自然语言摘要。
- 第1章默认只作为“请求体样式参考”读取；接口动作清单、字段含义表、PREP→QUERY 编排、查询分组与复用判断必须在 `stages/middlequery.md` 中实现，不得把主流程重新塞回第1章。
- 用户选择 `1` 并完成设计预览输出后，只有用户**严格回复** `继续开发`，才能进入实现阶段。
- 固定启动快照的 1/2/3/4 四段必须完整输出；不得用“阶段0预检完成”或其他摘要替代。

## 参考文件

- query-engine AI 用法：`/Users/xuey/Desktop/cncr-workplace/packages/query-engine/AI_USAGE.md`
- 设计阶段增强 Skill：`../cncr-design-aesthetic/SKILL.md`
- 契约定义：`references/canonical-contract.md`
- 回填矩阵规范：`references/fill-matrix-spec.md`
- 阶段文件：`stages/*.md`

## 脚本

- `scripts/scan_reuse.py`：扫描 API/组件复用候选并给出建议。
- `scripts/validate_mapping.py`：校验业务执行 MD 与生成代码是否一致，支持业务 MD 驱动的动态验收。
