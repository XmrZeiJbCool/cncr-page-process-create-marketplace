# cncr-page-process-create marketplace

## Structure
- `.claude-plugin/marketplace.json`: marketplace manifest
- `plugins/cncr-page-process-create-plugin/.claude-plugin/plugin.json`: plugin manifest
- `plugins/cncr-page-process-create-plugin/skills/cncr-page-process-create`: skill payload

## Local test
```bash
claude plugin validate /Users/xuey/Desktop/cncr-page-process-create-marketplace
claude plugin marketplace add /Users/xuey/Desktop/cncr-page-process-create-marketplace
claude plugin install cncr-page-process-create-plugin@cncr-marketplace
```

## Remove
```bash
claude plugin uninstall cncr-page-process-create-plugin
claude plugin marketplace remove cncr-marketplace
```
