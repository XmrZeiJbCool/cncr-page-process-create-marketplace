# 回填矩阵规范（Fill Matrix Spec）

> 格式：组件目标位 ← 契约字段 ← 转换规则
> 说明：本文件定义的是通用回填矩阵结构与验收原则，示例仅作说明，不构成固定业务范式。

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

## 4. 运行时验证输出（新增）

- 生成页面后，必须在运行时输出区域级回填验证结果，默认输出到浏览器控制台。
- 输出粒度基于真实生成区块，而不是固定组件 ID；至少覆盖：图表区、表格区、状态区。
- 推荐输出格式：
  - `图表1: 成功OK`
  - `表格1: 成功OK`
  - `状态区1: 成功OK`
- 若某区域未完成回填，应输出 `失败FAIL`，并附带失败原因（如缺少 `resultData.rows`、缺少 `display` 回退、缺少状态绑定）。
- 运行时输出必须在 `resultData` 完成归一化并传入 UI 后触发，不能只依赖离线脚本扫描。
