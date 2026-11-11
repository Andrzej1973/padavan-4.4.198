# Modern POST candidate checkpoint — 2026-11-11

This is isolated verification source. Production Modern remains read-only.

The candidate extends existing authenticated start_apply.htm and its CGI/NVRAM
pipeline. Marked requests require POST, one custom header, no URL query, actual
authentication even in trusted-local login state, one canonical positive decimal
Content-Length1..8192 and no Transfer-Encoding. Full body length, unique decoded
field names, valid escapes and one Modern version marker are checked before CGI.
The existing valid-percent decoder uses memmove with the source-tail length.
CGI cache and body are cleared after successful output; failed input is wiped.

The joined host fixture executes actual HTTP dispatcher, body callback, CGI,
request/service loop, variable apply, commit and notify functions under ASan/UBSan.
It covers24 band/shared/manual/keep/change/open cases and whole-request replay,
UTF8/escaping, namespace injection, duplicate/short bodies and authentication
rejection. It substitutes authentication computation/login state, sockets,
NVRAM/flash/RC operations and template expansion (using the exact callback order
from start_apply.htm).171 actual WLAN names/types are included, but event bits
remain fixture constants. This does not establish device runtime or full HTTP
server acceptance.

Run `PYTHONDONTWRITEBYTECODE=1 python3 tools/webui-preview/check_guest_candidate.py
<exact-source-tar>` on one line against the preserved c25283e source archive.
`check_json.py` runs pure C components. Optional CI compiles/links the complete
isolated HTTP package and checks credential/Guest/body guard strings and ELF.
It never installs the candidate or changes the production image.

Open requirements before Apply activation: exact target result for this package,
request freshness/concurrency policy, real browser/HTTP/template behavior,
structured response and retry semantics, safe radio/driver lifecycle, complete
UI validation/confirmation/error flows and physical acceptance at the agreed
later stage. Never equate committed settings or notification with running Wi-Fi.

Evidence: WR1200JS-MODERN-ENDPOINT-HOST-2026-11-11.json and earlier BODY-CGI,
TRANSPORT and REQUEST-SEQUENCE reports. Earlier candidate target31e7732 was
verified independently in CI988-989 evidence; it does not cover this body change.
Temporary source/C/binary trees were automatically removed; no firmware retained.
