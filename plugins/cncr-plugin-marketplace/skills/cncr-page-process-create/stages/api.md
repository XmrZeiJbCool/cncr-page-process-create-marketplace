# 阶段2：请求实现

## 目标
- 基于项目内能力、私仓能力和业务 MD 落实请求层实现。

## 必须输出
- 请求层实现来源（项目内复用 / `@cncr/query-engine` / 新建）
- 若未使用 `@cncr/query-engine`，必须说明原因
- 代理复用情况
- API 参数完整性验收结果
- 若使用 `@cncr/query-engine`，必须说明本次采用的导入入口与源码依据

## query-engine 文档依据（强制）
- 若请求实现采用 `@cncr/query-engine`，必须先读取并引用：
  - `/Users/xuey/Desktop/cncr-workplace/packages/query-engine/AI_USAGE.md`
  - `/Users/xuey/Desktop/cncr-workplace/packages/query-engine/README.md`
  - `/Users/xuey/Desktop/cncr-workplace/packages/query-engine/docs/queryMiddlelayer.md`
- 必须明确区分：
  - 常规场景：`@cncr/query-engine`
  - legacy 协议场景：`@cncr/query-engine/legacy`
- 若命中 legacy 场景，不得误用主入口替代 legacy 子入口。

## QueryMiddlelayer 边界说明（强制）
- 若请求实现识别为 `QueryMiddlelayer` 或 `createBroadtechLegacyQueryMiddlelayer`：
  - 第1章只作为请求体样式示例，不承担接口动作说明、字段说明或主流程编排职责。
  - API 阶段只负责确认“当前实现命中了 QueryMiddlelayer 能力边界”。
  - 区域级 `dataSetId` / `tblId` / `webModuleId`、字段合并、PREP→QUERY 编排、区域复用与回填关系，不得继续混写在本阶段，必须转交 `stages/middlequery.md` 专门处理。
- 若接口响应出现“模块ID为空”“无法获取权限信息”“权限不足”“参数缺失”等错误，API 阶段仍必须判定为 `API参数完整性: 失败FAIL`。
- 若请求实现不是 `QueryMiddlelayer`，则不得套用 QueryMiddlelayer 的固定规则，应改按当前查询方法的契约进行验收。

## 强约束
- `@cncr/query-engine` 是默认优先的请求实现来源。
- 未明确决定弃用前，禁止默认新建一套独立请求层。
