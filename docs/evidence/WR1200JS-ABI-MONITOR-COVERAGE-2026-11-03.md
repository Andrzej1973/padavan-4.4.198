# ABI failure monitor coverage gap

Failed ABI run: 41576328965, job 125720562794, step 102.
Original log identifies prepare-wds-outer-operation.py rejecting the stale
include/interface-reference.h hash. Fix ac37f05 updates that exact pin;
the complete peer preparation replay subsequently reached its final stage.

Read GitHub main's .github/workflows/monitor-agent.yml through the contents
API on 2026-11-03. Its workflow_run watched list includes firmware and service
checks, but omits Band Steering driver ABI. The shared working branch already
includes ABI and failure-only triggering. GitHub workflow_run uses default
branch workflow configuration; editing this branch alone does not activate it.

Monitor run 41577840912 is skipped and has no artifacts. It must not be
represented as a successful ABI failure report. No causal excerpt comparison
is possible because no report was produced for the ABI event.

Next operational fix is to review and land the existing monitor workflow
changes on main through the project handoff/review process. No main mutation,
merge, schedule restoration, Codex heartbeat or parser changes were performed
in this investigation. After landing, verify first real ABI failure creates
one bounded report with correct run/job/step; successful runs remain silent.
