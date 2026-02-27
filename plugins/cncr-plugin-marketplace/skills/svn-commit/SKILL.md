---
name: svn-commit
description: Use when the user mentions SVN operations like "update", "commit", "pull", or "push". Handles authentication, conflict resolution, and strict commit verification.
---

# SVN Commit & Update Workflow

## Response Prefix Rule

- Every user-facing response in this skill must start with `【CNCR_SKILLS】`.
- Use concise style after the prefix, e.g. `【CNCR_SKILLS】请提供 SVN 账号和密码。`.

## Overview
Strict workflow for SVN operations involving authentication handling, conflict resolution assistance, and pre-commit verification.

**Role**: Assistant (System)
**Addressee**: （无固定称谓）

## Workflow Selector

1. **Analyze User Intent**:
   - **Update** keywords: "更新", "update", "pull", "拉取" -> Go to [Update Workflow](#update-workflow)
   - **Commit** keywords: "提交", "commit", "push", "上传" -> Go to [Commit Workflow](#commit-workflow)

## Update Workflow

1. **Request Credentials**:
   - Explicitly ask: "【CNCR_SKILLS】请提供您的 SVN 账号和密码以执行更新。"
   - **WAIT** for user response.

2. **Execute Update**:
   - Run `svn update --username [user] --password [pass]`.

3. **Check Conflicts**:
   - Scan output for lines starting with `C`.
   - **If NO conflicts**: Report success with revision number. End.
   - **If conflicts**:
     - List all conflicting files immediately.
     - **Enter Resolution Loop** for each file:
       1. Show diff (Local/Mine vs Server/Theirs).
       2. Ask: "保留我的修改 (A), 使用服务器版本 (B), 还是手动合并 (C)?"
       3. Assist in applying the fix.
       4. Run `svn resolved <file>`.
     - **Verify**: Confirm all conflicts are resolved before reporting success.

## Commit Workflow

1. **Review Changes (Step 1)**:
   - Run `svn status`.
   - **Output Requirement**: Display changes in a **Markdown Table**.
     ```markdown
     | 状态 | 文件路径 | 描述 (简要推测) |
     | :--- | :--- | :--- |
     | M    | src/utils/auth.js | 修改 |
     | A    | src/components/Login.vue | 新增 |
     ```
   - **STOP**: Ask "【CNCR_SKILLS】请确认以上文件清单是否无误？"
   - **WAIT** for explicit confirmation ("确认", "没问题", "Yes").

2. **Credentials & Message (Step 2)**:
   - Ask: "【CNCR_SKILLS】请提供您的 SVN 账号和密码。"
   - **Commit Message Strategy**:
     - **User Provided**: If user already specified a message (e.g., "提交代码，备注修复bug"), **USE IT**.
     - **Not Provided**:
       - Analyze `svn diff`.
       - **Suggest** a message following `CLAUDE.md` types (`feat:`, `fix:`, `docs:`, etc.).
       - Phrase: "【CNCR_SKILLS】建议提交信息为: `type: message`。您是否采纳？或者请提供您的自定义信息。"

3. **Execute Commit (Step 3)**:
   - Run `svn commit -m "message" --username [user] --password [pass]`.
   - Report result with revision number.

## Important Rules
- **Address**: Always start responses with `【CNCR_SKILLS】`.
- **Security**: Do not store passwords. Use them only for the executed command.
- **Commits**: NEVER commit without the "Table Review -> User Confirmation" sequence.
