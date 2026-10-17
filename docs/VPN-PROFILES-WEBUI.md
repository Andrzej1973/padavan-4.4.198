# Independent VPN profiles — WebUI plan

Status: design only. No page, route or HTTP action is registered yet.
Requirement: `docs/PROJECT-DELIVERY-SCOPE.md`, "Distinct WG/AWG tunnel profiles".

## Scope

The WebUI must let the owner:

- see every stored profile with its protocol, label, revision and observed state;
- bring one profile up or down without touching the others;
- delete a stopped profile (stop and delete stay distinct actions);
- open the existing private export/QR for one profile.

Editing a configuration over HTTP is deferred to `wr-vpn-profile edit` until a
bounded upload path exists. The first iteration must not accept arbitrary
configuration bodies over HTTP.

## Endpoints

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `wr_vpn_list` (ej handler) | GET | JSON list: id, protocol, label, revision, state |
| `wr_vpn_state?id=N` (ej handler) | GET | observed link state and `plan` verdict for one profile |
| `wr_vpn_action.cgi` | POST | `up`/`down`/`delete` for one id, CSRF token and `ack=1` |

## Security rules (same shape as the USB/IP actions)

- Login required (`get_login_safe()`); mutations only over POST.
- 32-hex CSRF token from `/dev/urandom`, exposed by `wr_vpn_token`.
- `ack=1` confirmation for every mutation.
- Body limit 512 bytes; id parsed canonically (1–999); the protect list is
  bounded and validated by the CLI, never passed through a shell.
- Fixed executable `/usr/sbin/wr-vpn-profile`, bounded run time, one job at a
  time, result retained for 120 seconds and read back by id.
- `up` runs as a background job: DNS pinning and link creation can take seconds
  and must not block the HTTP worker.

## UI

A section on the existing VPN page lists profiles with state and three buttons
(up/down/delete). Delete is disabled while a session is live. Every label goes
through the EN/UK/RU dictionaries.

## Tests and gates

- Host fixture for the action argv and refusal paths (no shell, bad id, bad
  token, missing confirmation).
- `node` check that the page sends the token and `ack` and reads the job result.
- Image gate: route present, handler registered, page contains the section, and
  ROMFS contents unchanged unless the WireGuard selector is enabled.

## Non-goals

- Editing or importing configurations over HTTP.
- A "route all traffic" toggle.
- Enabling profiles from the UI at boot; nvram stays the single source.
