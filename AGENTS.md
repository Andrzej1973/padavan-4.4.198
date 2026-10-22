# Instructions for every project agent

Run Git normally. If a network operation fails with a proxy-related error,
follow the conditional, process-local troubleshooting steps in section 14 of
`docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md`. Do not routinely clear proxy
variables or change saved/system/global proxy settings.

For GitHub fetch/pull/push in this repository, use the SSH remote and follow
the shared transport rule in `docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md`.

For project context and the current executor, start with
`docs/AGENT-BOOTSTRAP.md` and `docs/EXECUTION-ROLE.md`.

## Shared Codex accounts and existing agent roles

This repository is one shared local checkout for sequential work by up to seven
Codex accounts. Sol and DeepSeek remain part of the existing project workflow;
their rules in `docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md` and the current role
record in `docs/EXECUTION-ROLE.md` remain in force. These instructions extend
that workflow and do not replace or transfer either role.
DeepSeek (also referred to by the owner as DeepSeeC) may join periodically;
keep that agent in the handoff process even when it is not the current writer.
Do not remove or overwrite its rules, Sol's rules, or the role history when
updating the seven-account Codex procedure.

At the start of every session, read `AGENTS.md`, `PROJECT_STATUS.md`,
`CODEX_HANDOFF.md`, `docs/AGENT-BOOTSTRAP.md`, and the current section of
`docs/EXECUTION-ROLE.md`; then inspect `git status --short --branch`. Preserve
all existing modified and untracked files. Never assume another account's
chat history, memory, authentication, or GitHub connection is shared.

## Router diagnostics across agents and accounts

For routine WR1200JS diagnostics, first check whether this executor is allowed
to run the fixed read-only helper `tools/wr1200js-readonly.ps1`. Use only its
named checks; never replace them with arbitrary remote command input. If the
executor blocks SSH or cannot access the owner's Windows SSH identity, do not
bypass the block, alter security settings, or claim that the device was
checked. Give the owner the exact PowerShell command for the needed named
check, ask them to run it in ordinary Windows PowerShell, and request the
complete output. Record the received output and its provenance in the shared
evidence/status files so the next agent can continue without repeating the
same setup. If another authorized project agent or the owner can already
perform the check, coordinate through the current handoff rather than starting
a parallel writer or duplicating device access. Router checks remain
read-only unless the owner explicitly approves a specific state-changing
operation.

Use the same existing checkout and branch. Do not create account-specific
clones or worktrees. Only one agent/account may make changes in this checkout
at a time, including Sol and DeepSeek. Before handing off, stop editing, record
the exact branch/HEAD, current task, checks, and next action in
`PROJECT_STATUS.md` and `CODEX_HANDOFF.md`. Do not stage or commit unrelated
work to make a handoff look clean.

Switch Codex accounts only through the desktop app's official sign-out/sign-in
flow. Never share or copy passwords, browser sessions, OAuth tokens, or
credential stores. Reopen the same local folder after signing in. Account
switching and opening the folder do not transfer chat history; the handoff
files are the shared project context.

The helper `tools/codex-shared-workspace/Check-SharedRepo.ps1` is read-only by
default. Its `-OpenInCodex` option asks the installed `codex app` launcher to
open this same checkout; it does not change Git or authentication settings.

## Board capability verification

Apply this rule to every router board/config added to this repository. Before
exposing a hardware feature in WebUI, verify its complete path for that exact
board: effective kernel/driver options, driver implementation, HTTP/NVRAM
acceptance and apply path, per-board defaults, and final image contents. A
chipset ID, generic capability helper, inherited menu item, or vendor feature
list alone is not evidence that the feature works. Record each capability in a
per-board manifest with status (`supported`, `unsupported`, or
`runtime-unverified`) and source/revision evidence. Unsupported controls must
be absent from that board's WebUI, rejected or rendered inert by its backend,
and disabled in defaults. Do not remove shared implementation needed by other
boards. Add a build-time check against the exact effective `.config` and final
ROMFS so the image fails closed when its manifest and exposed controls
disagree. Keep runtime validation distinct from source/build evidence. Run the
same review whenever a new board config is introduced.
