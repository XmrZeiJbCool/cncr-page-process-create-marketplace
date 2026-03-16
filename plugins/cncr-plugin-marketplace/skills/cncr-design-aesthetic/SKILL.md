---
name: cncr-design-aesthetic
description: CNCR 设计阶段增强 Skill；在 pencli MCP 设计预览前加载，约束画布、布局、卡片、按钮、空态、表格与反模式，稳定页面审美与结构表达
---

# cncr-design-aesthetic

用于 `pencli MCP` 设计预览阶段的审美增强与设计范式约束。

## 核心定位（强制）

- 本 Skill 不负责业务数据契约、接口流程或回填矩阵。
- 本 Skill 只负责设计阶段的视觉范式、布局稳定性、组件映射表达和反模式约束。
- 当主流程 Skill 进入设计预览阶段时，应先读取本 Skill，再调用 `pencli MCP` 出图。

## 设计阶段执行顺序（强制）

1. 读取业务执行 MD 的第3章 UI 定义
2. 读取 `references/AI_DESIGN_GUIDE.md`
3. 读取 `references/ANTI_PATTERNS.md`
4. 确认画布尺寸（未指定时默认 `1920x1080`）
5. 调用 `pencli MCP` 生成设计预览
6. 输出本次采用的设计依据与反模式规避结果

## 通用强规则

- 默认桌面画布为 `1920x1080`，并按该画布完整展开布局。
- 查询页、仪表盘页、统计页默认采用宽屏工作台式布局，不画成居中窄栏。
- 图表区、表格区、工具栏必须有明确容器感。
- 默认无数据态，不得在预览阶段主动填充假数据制造“看起来完整”的错觉。
- 表格默认必须有表头，主按钮默认蓝色圆角。
- 若存在 `.pen` 设计系统组件，优先用可复用组件；否则使用命名占位块表达真实代码组件。
- 必须主动规避 `references/ANTI_PATTERNS.md` 中定义的反模式。

## 输出要求

- 对用户明确说明：本次设计预览已加载 `cncr-design-aesthetic`
- 明确说明采用的画布尺寸
- 明确说明采用的关键设计范式
- 明确说明规避了哪些反模式

## 参考文件

- 设计范式：`references/AI_DESIGN_GUIDE.md`
- 反模式：`references/ANTI_PATTERNS.md`
