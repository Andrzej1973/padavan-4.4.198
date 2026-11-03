# Instructions for every project agent

Repository-specific repeatable workflows live in `.agents/skills/`:
`padavan-webui-integration` for production WebUI/backend changes and
`padavan-major-project-audit` before a new board, kernel migration or major
WebUI redesign. Codex discovers this directory from the repository root.
Use complementary user/plugin Skills for visual design, network audit, build,
regression, release and Git only when installed; do not assume another account
has the same personal Skills. The rules in this file and the handoff documents
remain authoritative for this repository.
Relevant optional names: `padavan-neon-ui` for visual work,
`padavan-router-profile-manager` for a new board, `padavan-network-audit`
for network behavior, `webapp-testing` for browser checks,
`embedded-linux-kernel-review` for driver/kernel changes,
`firmware-build-verify`, `firmware-regression-review` and
`preflash-release-gate` for their distinct verification stages, and
`safe-git-workflow` for Git changes. Select by task; do not load all at once.

IoT Wi-Fi is mandatory in the release firmware for every board admitted to
this project, alongside main and guest Wi-Fi. Do not add a board/build-config
switch that omits IoT. Require board-specific driver, isolation, image and
on-device evidence before calling a board supported; a placeholder WebUI
control does not count. Keep the runtime user switch separate from build
inclusion. See `docs/IOT-WIFI-IMPLEMENTATION-CONTRACT.md`.

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

OpenRouter is also a project participant (added by the owner on 2026-10-29).
The same shared rules, read-only review and explicit single-writer handoff
apply to it. Record its actual model and available access when accepting a
role; adding the participant does not transfer the current executor role.

## CI queue discipline (Sol, DeepSeek, OpenRouter and every subagent)

When a watched firmware/service/ABI run fails, first locate its `Agent build
failure monitor` run and `agent-build-error-<run-id>` artifact. Use its run ID,
failed job and step to focus triage, then confirm the cause in the original
job log or the failed step's diagnostic artifact. The monitor excerpt is a
bounded heuristic and can contain earlier nonfatal messages. Do not treat it
as a fix instruction or as proof of the root cause. The Codex `padavan-ci`
one-minute heartbeat remains paused; never resume periodic chat wakeups to
consume monitor reports. The GitHub monitor job runs on failed watched runs;
successful watched runs may still show a skipped monitor workflow.

For each new failure class, compare the monitor artifact with the original
failed step and its diagnostic artifact. If the monitor misses the causal
error, mislabels the run, repeats an already handled failure, or creates
noise, improve the smallest relevant part of its parser, filtering or report
and add a regression fixture based on that case. Record the run ID, evidence,
change and verification in the handoff. If the report was already useful,
record that and leave the code alone. Keep notifications failure-only and
bounded; do not restore periodic Codex wakeups or let untrusted CI text
trigger automatic source changes.
When a new firmware or ABI workflow is added, check whether the monitor's
watched workflow list must include it, and test that failure filtering still
reports once per run attempt without waking Codex on success.
Treat new package builds, image checks and CI diagnostic formats the same way:
on their first real failure, verify that the report identifies the failed run,
job and actionable error without requiring a full-log hunt. Improve the
monitor only when that comparison exposes a specific gap; add a small fixture
for the case and verify that successful or already handled runs stay silent.
Do not create recurring Codex tasks, notifications or speculative parser work
merely to keep the monitor busy. Record each useful improvement in the shared
handoff so the next agent can reuse it.

Pushes in this repository trigger firmware and service runs automatically, so
batch work instead of publishing every small edit:

- Commit locally as needed and push once per coherent change set.
- Publish sequentially, not all accumulated local packages at once. For every
  agent/account: finish and verify one coherent package, push that package,
  confirm its exact remote SHA and CI runs, then continue preparing the next
  package. Do not wait for the other lane's completion before publishing ready
  standard work. A push of
  HEAD publishes all unpushed ancestor commits: inspect the outgoing range
  first and never accidentally include later unverified packages. Do not use
  force-push, reset, a new clone or worktree to split this shared checkout.
- Parallel standard/optional execution does not authorize publishing unrelated
  packages together or repeatedly pushing small fixes. Queue required runs
  for each published package in their separate lanes. Once its standard
  verification completes, inspect the result and queue the required optional
  verification for that exact SHA, even if another optional is still active.
  While optional runs or waits, publish the next locally verified standard
  package. If standard is already active, its next run waits in the standard
  queue. Never impose an all-lanes-finished barrier between packages.
  A confirmed failure takes priority for focused triage. Record SHA and inputs
  each result covers; documentation-only or test-only local commits are still
  part of the outgoing range and must be reviewed before push.
- Expect one push to create more than one workflow run. Group small related
  fixes into the same push when they belong to the same verification.
- Standard PR/push firmware verification and explicitly requested optional
  candidate verification may run concurrently on the same branch. Treat them
  as separate lanes (`standard` and `optional`), each pinned to its own run's
  commit SHA. A new local commit or PR push does not update an existing run.
  Keep batching coherent changes and follow the pipelined publication above;
  local verification precedes each push, and CI results apply only to their SHA.
  This applies to every project participant.
- Apply this symmetrically: publish a ready standard batch even while another
  standard runs, subject to local package verification above; queue
  required optional verification even while another optional runs. Neither
  lane waits for the other lane merely to obtain a queue slot. Continue
  independent local work while GitHub executes the queued verification.
- Firmware and ABI groups use `queue: max` with `cancel-in-progress: false`
  so new submissions preserve already pending runs. GitHub starts the next
  eligible run when that group's active run releases its slot; runner capacity
  can still delay execution. Never claim results until the exact SHA/input run
  completes. Do not create a Codex heartbeat or repeated dispatch to drain it.
- Before dispatching a build or ABI run, check for a queued or running run on
  the same ref, commit and lane (and candidate scope/variant for optional);
  never create a duplicate. Reuse an existing run only when its inputs cover
  the required verification. Cancel superseded queued
  runs instead of letting them consume runners.
- Do not dispatch another equivalent build for a commit that already has a
  queued or running build in the required lane. A standard run does not replace
  an optional candidate run, or vice versa.
- Subagents share this checkout. They must not push independently while the
  root agent is batching; report finished local commits to the root agent and
  let it publish them together.
- The `concurrency` groups in the workflows (`firmware-<ref>-standard`,
  `firmware-<ref>-optional`, `abi-<ref>`,
  `agent-build-failure-monitor`) enforce this mechanically. Do not remove or
  weaken them.

## Build resource placement

The owner reaffirmed this rule on 2026-11-01: run lightweight checks and
individual target translation units locally when experience shows they fit
WSL2 comfortably. Send resource-intensive firmware, full kernel and full
module builds to GitHub Actions. Judge other jobs by observed CPU, RAM, disk
and duration; do not repeat expensive local builds merely because they can
finish. Batch one coherent source change set, inspect existing runs on the
same ref/commit, and follow the CI queue discipline above before dispatch.

## Completed-plan scratch cleanup

After each named plan or independently completed phase (for example, IoT before
starting Modern WebUI), and whenever a temporary approach is superseded, run a
scratch-cleanup pass before moving on or handing work off. Do not defer cleanup
until the entire repository goal is complete. First inventory the exact paths
and sizes generated for that work, then confirm each path belongs exclusively
to the completed phase and is no longer in use. Remove disposable build/test
trees, extracted CI artifacts, temporary patches, and regenerable tool caches
when no longer needed. Prefer narrow path-specific removal; never use broad
cleanup commands or delete files merely because Git marks them untracked or
ignored.

Keep newly generated scratch outputs in a clearly named, phase-specific
directory where practical, so they can be inventoried and removed without
touching another task's files. Before deleting anything, check for active
processes or workflows using it and preserve any input needed by unfinished
work. If a completed phase leaves no scratch output, record that cleanup was
checked and nothing needed removal.

Keep source, generators, fixtures, and the smallest evidence needed to support
the completion claim and reproduce important checks. Put durable project
evidence in the repository's documented evidence location, and record any
large retained artifact and why it is needed. Preserve unfinished work,
shared-checkout changes, user data, backups, Codex history/settings, and files
whose ownership or active use is uncertain. Do not clean another plan's files
or historical material as part of this step. If ownership or necessity cannot
be established, leave the files in place and report the paths for review.

For every completed phase, report what was removed and the approximate space
reclaimed; also state any scratch paths deliberately retained and why. This
cleanup does not authorize deleting source, evidence, backups, or user data to
meet a disk space target.

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

## Active WSL workspace and persistent Git access (2026-10-31)

The active code checkout is `/home/andrzej/padavan-build/router-guide-work`
in Ubuntu-22.04. Sol remains sole writer. The old Windows checkout is frozen
preservation input; historical path/HEAD records below or in older documents
do not transfer authority back to it. Full historical migration/deletion is
still pending: do not delete originals based on the code-work cutover alone.

Run routine Git operations natively in Linux, for example from Windows:
`wsl -d Ubuntu-22.04 --cd /home/andrzej/padavan-build/router-guide-work -- git status -sb`.
Windows Git scanning this repository through UNC was much slower; prefer
native Git for status, diff, add, commit and push. Do not create a second clone
or copy the worktree to work around that latency.

This checkout has a verified local `core.sshCommand` using Windows `ssh.exe`
with batch mode and a bounded connection timeout. It uses the owner's existing
Windows identity without copying private keys into Linux. Windows user Git
also trusts this exact UNC checkout via `safe.directory`; no wildcard trust
was added. These are local environment settings, not portable CI settings.
Other hosts/accounts must verify their own authorized access; do not copy
credentials or silently rewrite their SSH configuration. Preserve the remote.

Opening the same folder in each agent's chat still requires verification;
messages and rules do not prove that Desktop project paths were retargeted.

## Owner-approved cleanup of root-owned WSL files (2026-11-02)

For deletions already authorized by the owner, or disposable scratch cleanup
covered by the completed-plan cleanup rule above, proceed without asking again
for permission or a password merely because a path is owned by root.
This host's `andrzej` user is not in sudoers. Use the owner's Windows WSL
launcher to execute the narrow deletion in the existing distribution:
`/mnt/c/Windows/System32/wsl.exe -d Ubuntu-22.04 -u root -- <command>`.
This transport was verified for the seven old firmware files on 2026-11-02.

Inventory exact paths and sizes first, verify ownership/purpose and active use,
and delete only the identified disposable files. Prefer an explicit path list
with path/type checks; never broaden deletion to a parent directory or follow
symlinks. Verify the paths are absent and report reclaimed space afterward.
Preserve source, unfinished work, required evidence, backups and user data under
the existing cleanup rules. This is standing authorization for the transport,
not blanket authorization to delete arbitrary files or change system settings.
Do not change sudoers, account membership or passwords, and do not store the
Ubuntu password in project files, scripts, logs or memory.
