# HTTP edit parser through actual RC configuration ownership

The existing eight-mode `check-config-edit-route.py` fixture now feeds its
requests through the actual `wr_iot_http_edit_request_read()` implementation
before submitting them with the actual control client and mailbox. Previous
versions constructed the client fields directly and tested the parser elsewhere.

The composed fixture passed with strict GCC, ASan and UBSan:

- Unauthenticated, GET and mismatched-CSRF forms refuse without changing the
  parsed output or causing writes/commits.
- Form decoding produces the intended SSID, subnet and KEEP/REPLACE intent.
  The endpoint supplies the mode; the parser does not accept a transaction
  identity from the form, and the client assigns the queue identity.
- Actual RC lease/pin resolution, RAM and AUTO/explicit Save owners, native
  snapshot parsing and the forked worker retain their existing checks for
  stale/superseded/expired revision refusal, manual RAM-only policy and unknown
  outcomes without replay. Native flash, clock, entropy and SDK are test actors.

This joins parsing and RC ownership in a host fixture. It does not run the
native HTTP server, prove its authentication implementation, exercise an actual
browser or accept the router. Production HTTP route preparation is checked by
the separate pinned-source fixture.

These test edits accompany the Classic candidate navigation package; they are
not in the earlier746ea2cc or its CI. No extra firmware run was dispatched solely
for this test change. Optional1377 independently verified the older13ce5dff
edit/view and Classic candidate image; see the separate image audit report.
