# 阶段6：运行时验证输出

## 目标
- 在运行时输出区域级回填验证结果，默认输出到浏览器控制台，并与静态校验结果形成双重验证。

## 必须输出
- 图表区 / 表格区 / 状态区的区域级日志
- 成功OK / 失败FAIL
- 失败原因
- Python 静态校验结果摘要
- Middlequery 查询组与区域映射摘要

## Python 静态校验（强制）
- 必须执行 Skill 内的 Python 校验脚本，并输出其结果摘要。
- 至少需要回报以下字段：
  - `valid`
  - `issues`
  - `area_fill_summary`
  - `query_middlelayer_detected`
  - `missing_query_middlelayer_fields`
  - `query_middlelayer_error_tokens`
- 若用户要求“打印验证结果”，不得只写自然语言结论，必须把上述结果带入报告。

## 推荐格式
- `图表1: 成功OK`
- `表格1: 成功OK`
- `状态区1: 成功OK`
- `查询组Q1: PREP成功 / QUERY成功`
- `Python校验: valid=true`
