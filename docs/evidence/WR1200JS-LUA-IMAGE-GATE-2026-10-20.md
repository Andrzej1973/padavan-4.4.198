# Lua image audit extension — 2026-10-20

Build #492's independently downloaded BusyBox report explicitly excludes
`etc_ro/lua/5.1/share/json2lua.lua` and `lua2json.lua` from shell syntax coverage.
Pinned source `vipshmily/padavan-4.4` at
`c25283e915a2a00a763774dd255b14aff997285e` was inspected through GitHub API:
`trunk/user/lua51/Makefile`, both converter scripts under
`lua-cjson-2.1.0/lua/`, and `lua-5.1.5/src/luaconf.h`.

The package installs Lua 5.1.5, liblua, cjson.so, nixio.so and Lua utilities.
Both converters require cjson and cjson.util. Compiled module paths use
`/etc_ro/lua/5.1/share` and `/etc_ro/lua/5.1/lib`.

`tools/target_lua_audit.py` now runs from the existing exact-image BusyBox gate
when LUA is selected. It verifies executable Lua and native-module ELF/library
closure, compiles every shipped Lua source without executing it, and executes
the actual converters under target QEMU with clean environment and cwd.
Roundtrip data covers strings, numbers, booleans, an array and a nested object.
Malformed JSON and malformed Lua must return failure. Report failures feed the
existing build gate; stderr is bounded and preserved for diagnosis.

Local verification: Python AST parsing and selected-file diff checks pass.
Windows WSL did not provide a usable Linux execution environment, so no local
MIPS/QEMU execution is claimed. The new gate awaits a CI image run. No script,
interpreter, router configuration or production service behavior was changed.
Nixio syscall behavior, converter consumers and full service lifecycle coverage
remain open even if this bounded converter check passes.

## Build #493 fixture correction

Run `39446255382` failed in the new Lua gate before interpreter execution.
Downloaded artifact `12275803414` reports: `Dynamic executable has no interpreter:
candidate:etc_ro/lua/5.1/lib/cjson.so`. The gate incorrectly submitted dlopen
libraries as executable seeds. The closure API now accepts explicit shared
library seeds while preserving PT_INTERP requirements for executable candidates,
MIPS ELF/type checks, image-only dependencies and path guards.

The in-memory regression passes valid shared-library closure and rejects a
dynamic executable without interpreter, a missing dependency, and an escaping
library path. It writes no fixture directories. The normal image-audit step
runs this regression before QEMU checks. Actual Lua converter execution still
requires the next successful CI image result. This fixes the harness; it does
not establish that the shipped converters work.
