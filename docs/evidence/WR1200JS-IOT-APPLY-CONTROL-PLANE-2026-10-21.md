# WR1200JS IoT authenticated Apply control-plane audit — 2026-10-21

## Pinned source and scope

Inspected the Padavan base at
[`c25283e915a2a00a763774dd255b14aff997285e`](https://github.com/vipshmily/padavan-4.4/tree/c25283e915a2a00a763774dd255b14aff997285e), specifically
`trunk/user/httpd/web_ex.c`, `trunk/user/httpd/httpd.c`,
`trunk/user/rc/rc.c`, and `trunk/user/httpd/variables.c`. This is source-level
control-flow evidence only. No repository source, router, or running service
was changed in this audit.

## Confirmed control flow

- The pinned `web_ex.c` registers `apply.cgi*` with `do_apply_cgi` and
  `need_auth=1`. `httpd.c` checks authentication before invoking a protected
  request's input/output handlers.
- `do_apply_cgi` reads `action_script`, processes registered form values
  through the selected variable service table, then calls `sys_script(script)`
  and redirects. `validate_cgi` uses `nvram_set`, so values can be changed in
  running NVRAM before a separate RC notification has completed.
- `sys_script` has a general `/tmp/<name>` execution fallback for otherwise
  unrecognized script names. An IoT integration must add an exact, fixed
  `wr_iot_apply` dispatch branch and must never pass user-provided script text
  to a shell or rely on that fallback.
- The RC daemon's `handle_notifications()` consumes notification files and
  dispatches known names. The IoT candidate currently has no production RC
  notification handler or caller for `wr_iot_activation_start/stop()`.
- At the time of the initial audit, `wr_iot_request_stage()` read active-form
  NVRAM names. The later candidate change now maps only seven
  `wr_iot_request_*` names to the validated request before writing temporary
  `*_t` fields. This protects the active profile from an early form write,
  but it does not make ordinary `apply.cgi` a transactional IoT controller.

## Follow-up: generic Apply cannot report IoT activation result

The inspected `update_variables_ex()` path calls `validate_asp_apply()` for
`Apply` and may then process `action_script`. Its script branch calls
`sys_script(script)`, emits `done_committing()` and returns without an IoT
activation result. The separate `apply_cgi()` path calls `validate_cgi()` on
registered fields before its script branch; `validate_cgi()` immediately uses
`nvram_set`. A redirect or `done_committing()` therefore establishes only that
the request path ran, not that the third BSS, bridge, DHCP, firewall and DNS
became usable. The script name also reaches the general `/tmp/<name>` fallback
unless an exact dispatch branch is installed.

Consequently the IoT form must use a dedicated authenticated submission path
or an equivalent guarded branch that validates the entire allowlisted request,
serializes the candidate write with activation, invokes only a fixed RC
operation, and returns an observed success/failure status. Merely registering
`wr_iot_request_*` in a generic service table and setting `action_script` is
insufficient. This is a source-level finding from the pinned WebUI flow; no
production handler has been added yet.

## Required integration shape

1. Keep the form behind an authenticated route. Validate the complete fixed
   allowlist before any candidate write and serialize submission with RC
   activation. Store submitted values separately from the active profile.
2. Dispatch one fixed `wr_iot_apply` operation through an explicit HTTPD
   branch to an RC handler that owns the transaction and serialized activation
   lifecycle. Do not use the generic `action_script` success callback as an
   activation acknowledgement.
3. Bind candidate validation, pre-change snapshots, activation, observed
   status, commit-on-success and retained rollback-on-failure. The backend
   must connect the real RC profile/radio, owned bridge/BSS, DHCP/DNS,
   quarantine/firewall/NAT, and recovery primitives already under development.
4. Add an authenticated status path that reports observed state and retained
   recovery state; do not infer success from saved NVRAM flags or a redirect.
5. Keep the firmware workflow's current IoT exclusion until source gates,
   image gates and device acceptance prove the complete path.

This narrows the missing production integration point. It does not establish
that the IoT activation or recovery path is implemented or safe to ship.
