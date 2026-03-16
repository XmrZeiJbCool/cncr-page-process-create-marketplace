# 阶段1：扫描与决策

## 目标
- 扫描项目内复用、私仓复用与新建实现三类候选。
- 输出“扫描结果 + 最终决策”，但不夹带业务范式。

## 必须输出
- 项目内复用结果
- 私仓复用结果
- 最终决策（项目内复用 / 私仓复用 / 新建实现）
- 若涉及请求实现，必须说明是否采用 `@cncr/query-engine`
- 若采用 `@cncr/query-engine`，必须说明 `AI_USAGE.md` 阅读结果

## query-engine 读取规则（强制）
- 一旦扫描结果命中 `@cncr/query-engine`，必须优先读取：
  1. `/Users/xuey/Desktop/cncr-workplace/packages/query-engine/AI_USAGE.md`
  2. `/Users/xuey/Desktop/cncr-workplace/packages/query-engine/README.md`
  3. `/Users/xuey/Desktop/cncr-workplace/packages/query-engine/docs/INDEX.md`
  4. `/Users/xuey/Desktop/cncr-workplace/packages/query-engine/docs/queryMiddlelayer.md`
- 必须基于上述文档输出：
  - 推荐导入入口
  - 推荐修改入口
  - 是否命中 legacy 场景
- 未读取上述文档前，不得直接新建请求实现。

## 禁止事项
- 禁止把业务 MD 里的具体页面范式写成通用规则。
- 禁止跳过私仓检查直接新建。
