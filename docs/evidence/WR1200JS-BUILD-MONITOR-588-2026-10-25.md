# Failure monitor use for build #588 (2026-10-25)

- Firmware candidate run [#588](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40195811064) failed at `Compile isolated merged IoT MT7603 candidate`.
- [Agent build failure monitor #224](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/40197404410) ran only because a watched run failed and uploaded `agent-build-error-40197404410`. That report identified build #588, attempt 1, commit `6d67414`, failed job and failed step.
- Its old first-256-KiB excerpt missed the decisive compiler line. The separate `iot-merged-driver-probe/build.log` established `ap_cfg.c:15059:8: error: void value not ignored as it ought to be`; source review found the stale `VOID ApCli_Remove` declaration. The candidate correction is commit `3ee7220`.
- `tools/agent-nim/build_monitor.nim` now reads at most 16 MiB per job and retains the latest 60 matching lines. An offline fixture with a late compiler error passed, and a live read-only recheck of #588 returned the actual `void value not ignored` diagnostic with `complete download` status. This is diagnostic help, not automatic Codex wake-up or automatic repair.
- The Codex `padavan-ci` heartbeat remains `PAUSED`, so it does not interrupt the chat each minute. The GitHub monitor workflow is triggered by completed watched runs, with its job gated on failure; successful runs may create a skipped workflow entry.

The GitHub monitor checks out `main`. The improved Nim extractor is local until published and will not affect that runner until it reaches `main`. Agents can still read the existing monitor artifact as a pointer and the original failed job log as evidence.
