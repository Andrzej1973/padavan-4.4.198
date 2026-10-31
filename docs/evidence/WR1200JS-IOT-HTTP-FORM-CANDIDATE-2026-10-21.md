# WR1200JS IoT dedicated HTTP form candidate — 2026-10-21

The pinned WebUI has an authenticated CGI handler pattern, but its generic
`apply.cgi` writes registered NVRAM fields before RC activation and can report
`done_committing()` without an observed IoT result. The separate USB/IP CGI
shows how to use an authenticated route, bounded POST input, a POST-method
check and a CSRF token. These are source patterns, not an installed IoT route.

`tools/iot/http-form.h` now supplies a no-write parser for a bounded
URL-encoded request. It accepts exactly seven named candidate fields plus a
token, refuses duplicate or unknown names, malformed encoding, control/NUL
bytes, oversized values, an invalid enable value and an absent or nonhex
32-character token. Enabled requests must contain all seven candidate fields;
disabled requests need only enable and token. The form adapter returns the
existing logical field names to `wr_iot_request_read()` for the existing
credential/subnet/mode validation. It does **not** authenticate a user,
compare the CSRF token, validate live routing, write NVRAM, send RC work or
claim activation success. Those operations belong to the future dedicated
authenticated handler and serialized RC backend.

`tools/iot/check-http-form.c` covers valid encoded UTF-8, disabled requests,
field access, missing fields, duplicates, unknown names, malformed escapes,
NUL, token shape, trailing separators and an oversized body. MinGW GCC
compiled it with `-std=gnu11 -Wall -Wextra -Werror -O2`; the executable
returned `PASS IoT HTTP form: fixed fields, bounded decoding,
duplicate/malformed refusal, no writes`. The local executable was removed.
The candidate source is not prepared into the production image, and the
router was not changed.
