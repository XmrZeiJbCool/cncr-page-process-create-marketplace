# CNCR 技能包 Marketplace

## 目录结构
- `.claude-plugin/marketplace.json`：Marketplace 清单
- `plugins/cncr-plugin-marketplace/.claude-plugin/plugin.json`：插件清单
- `plugins/cncr-plugin-marketplace/skills/`：技能包目录（核心 + 预留槽位）

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
