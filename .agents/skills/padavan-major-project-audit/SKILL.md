---
name: padavan-major-project-audit
description: Audit skills, repository evidence, board capabilities, risks and verification before a new router platform, kernel migration or major Padavan WebUI redesign. Skip for small isolated edits.
---

# Major-project start audit

1. Identify the exact task, repository, branch, board revision, architecture, existing changes and constraints. Read `AGENTS.md`, `docs/AGENT-BOOTSTRAP.md`, current status and handoff files.
2. Inventory available repository, user and plugin Skills by description; read only those relevant to the project. A cached plugin or archived file is not proof that a Skill is active. Avoid duplicate names and copied global procedures.
3. Check board/profile data against effective configs, board source, drivers and recorded device evidence. Record unknowns. Use the existing board capability files; do not invent a new profile format or borrow another model's hardware values.
4. For missing guidance, inspect repository Git history or known backups. Read a former Skill as reference if sufficient; restore or add only a specific necessary Skill after checking dependencies and impact on other projects.
5. Produce a scoped plan: owner, sequence, affected files, compatibility risks, source checks, target build/image checks, and separately authorized device validation. Do not begin implementation merely because this audit was run.

Run this before large architecture or platform work, not before every ordinary edit.
