# 回填矩阵规范（Fill Matrix Spec）

> 格式：组件目标位 ← 契约字段 ← 转换规则

## 1. 标准列定义

| 列名 | 必填 | 说明 |
|---|---|---|
| `componentId` | 是 | 组件唯一标识 |
| `targetPath` | 是 | 组件回填位置（如 `series[0].data`） |
| `sourceField` | 是 | canonical 字段路径（如 `canonical.chartData`） |
| `transform` | 否 | 转换函数名/规则 |
| `emptyFallback` | 否 | 空值回退策略 |
| `errorFallback` | 否 | 错误回退策略 |

## 2. 示例（ABC三图）

| componentId | targetPath | sourceField | transform | emptyFallback | errorFallback |
|---|---|---|---|---|---|
| `chartA` | `series[0].data` | `canonical.chartData` | `identity` | `[]` | `showError` |
| `chartB` | `xAxis.data` | `canonical.chartData[].name` | `pluckName` | `[]` | `showError` |
| `chartC` | `series[0].data` | `canonical.chartData[].value` | `toNumberList` | `[]` | `showError` |

## 3. 必检项

- 每个可视组件必须存在至少1条回填规则。
- `sourceField` 必须来自 canonical，不能是原始接口路径。
- 必须声明空数据与错误态行为。
