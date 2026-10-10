#!/usr/bin/env python3
"""Serve static JSON catalogues that ported WebUI pages fetch from /www.

The pinned mime_handlers table has no JSON entry, so /dot.json (Stubby),
/doh.json (DoH) and /amneziawg.json answered 404 and their pages showed
empty provider lists. Exact-name dynamic JSON routes stay ahead of this one.
"""
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "trunk/user/httpd/web_ex.c"
text = path.read_text(encoding="utf-8")
anchor = '\t{ "**.svg", "image/svg+xml", NULL, NULL, do_file, 0 }, // 2016.04 Volt1\n'
if text.count(anchor) != 1 or '"**.json"' in text:
    raise SystemExit("Inspect mime_handlers image anchor before adding the JSON route")
route = ('\n\t/* cached static JSON catalogues, same authentication as scripts */\n'
         '\t{ "**.json", "application/json", NULL, NULL, do_file, 1 },\n')
path.write_text(text.replace(anchor, anchor + route, 1), encoding="utf-8")
print("Added authenticated static JSON route after cached images")
