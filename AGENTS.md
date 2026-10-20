# Instructions for every project agent

Run Git normally. If a network operation fails with a proxy-related error,
follow the conditional, process-local troubleshooting steps in section 14 of
`docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md`. Do not routinely clear proxy
variables or change saved/system/global proxy settings.

For GitHub fetch/pull/push in this repository, use the SSH remote and follow
the shared transport rule in `docs/AGENT-HANDOFF-RULES-SOL-DEEPSEEK.md`.

For project context and the current executor, start with
`docs/AGENT-BOOTSTRAP.md` and `docs/EXECUTION-ROLE.md`.

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
