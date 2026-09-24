---
description: Automatically record and update task workflows and architectural changes in CHANGELOG_WORKFLOW.md
---

# Workflow & Change Logging Rule

Whenever any modification, bug fix, model update, or architectural adjustment is made to the codebase:

1. **Maintain CHANGELOG_WORKFLOW.md:**
   - Every time an issue is resolved, a setting is adjusted (e.g. Gemini model, CORS, endpoints, timeouts), or a feature is added, automatically append a detailed workflow entry to `CHANGELOG_WORKFLOW.md`.

2. **Entry Format Requirements:**
   Each log entry must clearly outline:
   - **Task / Goal:** What was requested or attempted.
   - **Issue Encountered (if applicable):** The exact error message or unexpected behavior.
   - **Root Cause Analysis:** Why the issue occurred or why the architectural change was needed.
   - **Changes Applied:** Specific files and lines modified, showing before and after context.
   - **Verification:** How the solution was validated (e.g., test output, curl/fetch results, build status).

3. **Autonomous Execution:**
   - Do this proactively and automatically without waiting for the user to explicitly remind you.
