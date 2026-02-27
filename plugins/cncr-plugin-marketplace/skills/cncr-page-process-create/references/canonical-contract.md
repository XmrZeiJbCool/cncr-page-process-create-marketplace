# 标准数据契约（Canonical Contract）

> 目的：屏蔽接口差异，保证 UI 回填稳定。

## 1. 最小契约（必须）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `queryId` | string | 是 | 查询会话标识 |
| `chartData` | array<{name:string,value:number}> | 是 | 图表标准数据 |
| `loading` | boolean | 是 | 加载状态 |
| `errorMessage` | string | 否 | 错误信息 |

## 2. 扩展契约（可选）

| 字段 | 类型 | 说明 |
|---|---|---|
| `legendData` | string[] | 图例 |
| `tableRows` | object[] | 表格回填数据 |
| `kpiCards` | object[] | 指标卡回填数据 |

## 3. 映射规则

- 第2章必须提供“源字段路径 → 契约字段”映射表。
- 缺失字段必须声明默认值与降级策略。
- 任何转换逻辑（聚合、重命名、格式化）必须显式说明。

## 4. 禁止事项

- 禁止 UI 直接消费接口原始字段。
- 禁止把接口特定字段名写死到第4章回填矩阵。
