# Phase 1A preparation — 2026-11-08

## Preservation review — 2026-11-21

This is a historical preparation note and a proposal for a separate next stage.
It does not authorize extraction or source moves during the merge audit.
The existing generator was executed against the current workflow into a
temporary report:272 textual calls,259 distinct paths and4 inline Python
blocks. Its workflow hash matched, and source_moves was empty. Thirty paths
did not resolve from the repository root; several are explicitly relative to
a changed shell directory or an assembled checkout. These are unresolved
static references, not evidence of broken workflow commands. Resolving cwd,
conditions and assembled/generated inputs remains the next-stage task.
The temporary report was removed. The historical detailed inventory stays local.

The owner requested considering the next phase after toolchain comparison.
The safe preparatory part has started: inventory actual build transformation
call sites before extracting shared code. The Phase 1 package was subsequently reviewed and published on main; see
REPOSITORY-MIGRATION-REPORT.md. Publication does not imply full release-variant
acceptance or authorize a bulk tree move.

The historical local build call-site inventory recorded243 textual calls to232
distinct Python/Node/shell script paths,
workflow line order, step labels, file existence, hashes and dirty-worktree
status. [The generator](../tools/repository/inventory-build-calls.py) is read-only
and uses the standard library. Four inline Python invocations are recorded
separately; subprocesses, shell conditions, cwd changes and variable-expanded
paths still require manual tracing. This is not a complete execution graph.

Next, trace the source assembly, board defaults, feature transforms, effective
config, compilation and image checks as distinct stages, retaining their real
caller/anchor preconditions. Extract shared code only after proving equivalent
inputs and outputs for existing WR1200JS; Mi Mini/Mi-4 remain pending. The
[toolchain review](WR1200JS-TOOLCHAIN-TRANSITION-REVIEW-2026-11-08.md) is an
independent prerequisite to compiler selection, not a reason to alter board
hardware or IoT lifecycle. No runtime source was moved in this preparation.
