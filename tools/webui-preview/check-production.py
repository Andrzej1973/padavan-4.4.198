#!/usr/bin/env python3
"""Validate a prepared production Modern WebUI tree without claiming compilation."""
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
a=p.parse_args()
root=a.source.resolve(strict=True)
web_ex=(root/'trunk/user/httpd/web_ex.c').read_text(encoding='utf-8')
modern=root/'trunk/user/www/modern'
index=(modern/'index.html').read_text(encoding='utf-8')
app=(modern/'app.js').read_text(encoding='utf-8')
wifi=(modern/'wifi.js').read_text(encoding='utf-8')
schema=json.loads((modern/'wifi-schema.json').read_text(encoding='utf-8'))

assert web_ex.count('static void do_wr_modern_json(')==1
assert '{ "wr_modern.json", "application/json", no_cache_IE, NULL, do_wr_modern_json, 1 }' in web_ex
assert 'do_wr_modern_json' in web_ex[:web_ex.index('struct mime_handler mime_handlers[]')]
assert '/api/dashboard.json' not in app
assert 'fetch("/wr_modern.json"' in app
assert "fetch('/modern/wifi-schema.json'" in wifi
assert schema.get('demo') is False

class Assets(HTMLParser):
 def __init__(self): super().__init__(); self.paths=[]; self.forms=0
 def handle_starttag(self,tag,attrs):
  values=dict(attrs)
  if tag=='form': self.forms+=1
  for key in ('href','src'):
   value=values.get(key,'')
   if value.startswith('/modern/'):
    self.paths.append(urlsplit(value).path)

parser=Assets();parser.feed(index)
assert parser.forms==0
assert 'ЛОКАЛЬНЕ DEMO' not in index
assert '<span class="demo-chip">DEMO</span>' not in index
assert 'PADAVAN MODERN · LIVE READ-ONLY' in index
for path in parser.paths:
 relative=path.removeprefix('/modern/')
 assert (modern/relative).is_file(),path
assert 'https://fonts.' not in index
assert 'http://' not in index
assert "location.hash" in app and 'renderGenericPage' in app
assert (modern/'shared-wifi.js').is_file()
print('PASS production Modern static shell and authenticated live JSON route structure')
