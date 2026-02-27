# CNCR 技能包 Marketplace

## 目录结构
- `.claude-plugin/marketplace.json`：Marketplace 清单
- `plugins/cncr-plugin-marketplace/.claude-plugin/plugin.json`：插件清单
- `plugins/cncr-plugin-marketplace/skills/`：技能包目录（核心 + 扩展 + 预留槽位）

## 当前技能清单
- `cncr-page-process-create`（核心）
- `svn-commit`（扩展）
- 输出规范：所有技能执行回复需以 `【CNCR_SKILLS】` 开头

## 本地验证
```bash
claude plugin validate /Users/xuey/Desktop/cncr-page-process-create-marketplace
claude plugin marketplace add /Users/xuey/Desktop/cncr-page-process-create-marketplace
claude plugin install cncr-plugin-marketplace@cncr-marketplace
```

## 远端安装（GitHub）
```bash
claude plugin marketplace add XmrZeiJbCool/cncr-page-process-create-marketplace
claude plugin install cncr-plugin-marketplace@cncr-marketplace
```

## 卸载
```bash
claude plugin uninstall cncr-plugin-marketplace
claude plugin marketplace remove cncr-marketplace
```
