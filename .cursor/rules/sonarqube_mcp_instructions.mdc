---
description: SonarQube MCP Server usage guidelines in Cursor. Situational — sonar home-lab docs, sonar-project.properties, quality rule/skill, or session sonar-mcp / @.
globs:
  - docs/ops/SONARQUBE_HOME_LAB.md
  - docs/ops/SONARQUBE_HOME_LAB.pt_BR.md
  - sonar-project.properties
  - .cursor/rules/quality-sonarqube-codeql.mdc
  - .cursor/skills/quality-sonarqube-codeql/SKILL.md
  - tests/test_sonarqube_python.py
alwaysApply: false
---

## When this rule attaches (Cursor)

**Context:** **`alwaysApply: false`** — loads when a path matches the **`globs`** above **or** the operator types **`sonar-mcp`** **or** attaches **`@sonarqube_mcp_instructions.mdc`**. **`.cursor/rules/quality-sonarqube-codeql.mdc`** stays the **in-repo** Python/markdown quality bar; this file is **MCP tool etiquette** + home-lab reachability.

**Companion:** **`docs/ops/OPERATOR_AGENT_COLD_START_LADDER.md`** § *Token → rule latch (`sonar-mcp`)*.

**Rollback:** `git revert` the commit or `git show <parent>:.cursor/rules/sonarqube_mcp_instructions.mdc`.

---

These are guidelines when using the **SonarQube MCP** server in Cursor. **Deploying** your own SonarQube (home lab, Docker, CI networking, tokens) is documented in **[docs/ops/SONARQUBE_HOME_LAB.md](../../docs/ops/SONARQUBE_HOME_LAB.md)** ([pt-BR](../../docs/ops/SONARQUBE_HOME_LAB.pt_BR.md)).

**Before MCP works:** the SonarQube instance must be **running**, reachable from the machine running Cursor, and authenticated with a **user token** (not a project token). GitHub-hosted CI needs either a **public/reachable** `SONAR_HOST_URL` or a **self-hosted runner** on the same LAN as SonarQube — see the home-lab guide §6.

---

These are some guidelines when using the SonarQube MCP server.

# Important Tool Guidelines

## Basic usage
- **IMPORTANT**: After you finish generating or modifying any code files at the very end of the task, you MUST call the `analyze_file_list` tool (if it exists) to analyze the files you created or modified.
- **IMPORTANT**: When starting a new task, you MUST disable automatic analysis with the `toggle_automatic_analysis` tool if it exists.
- **IMPORTANT**: When you are done generating code at the very end of the task, you MUST re-enable automatic analysis with the `toggle_automatic_analysis` tool if it exists.

## Project Keys
- When a user mentions a project key, use `search_my_sonarqube_projects` first to find the exact project key
- Don't guess project keys - always look them up

## Code Language Detection
- When analyzing code snippets, try to detect the programming language from the code syntax
- If unclear, ask the user or make an educated guess based on syntax

## Branch and Pull Request Context
- Many operations support branch-specific analysis
- If user mentions working on a feature branch, include the branch parameter

## Code Issues and Violations
- After fixing issues, do not attempt to verify them using `search_sonar_issues_in_projects`, as the server will not yet reflect the updates

# Common Troubleshooting

## Authentication Issues
- SonarQube requires USER tokens (not project tokens)
- When the error `SonarQube answered with Not authorized` occurs, verify the token type

## Project Not Found
- Use `search_my_sonarqube_projects` to find available projects
- Verify project key spelling and format

## Code Analysis Issues
- Ensure programming language is correctly specified
- Remind users that snippet analysis doesn't replace full project scans
- Provide full file content for better analysis results
