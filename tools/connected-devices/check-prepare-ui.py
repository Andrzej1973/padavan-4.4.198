#!/usr/bin/env python3
"""Check installation against an actual source homepage in a temporary copy."""
import argparse
import subprocess
import sys
import shutil
import uuid
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
a = p.parse_args()
local = Path(__file__).resolve().parent
relative = Path('trunk/user/www/n56u_ribbon_fixed/index.asp')
original = (a.source / relative).read_text(encoding='utf-8')
http = (a.source / 'trunk/user/httpd/web_ex.c').read_text(encoding='utf-8')

assert '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">' in original
assert '{ "**.js",  "text/javascript", no_cache_IE, NULL, do_ej, 1 }' in http
assert '{ "**.css", "text/css", NULL, NULL, do_file, 0 }' in http
assets = ['classify', 'refresh', 'homepage', 'roaming', 'roaming-view', 'boot']
asset_bytes = 0
for name in assets:
    data = (local / (name + '.js')).read_bytes()
    assert b'<%' not in data, 'Static JavaScript must not invoke the EJ template parser'
    asset_bytes += len(data)
asset_bytes += (local / 'homepage.css').stat().st_size
root = Path.cwd() / ('homepage-check-' + uuid.uuid4().hex)
assert root.resolve().parent == Path.cwd().resolve()
root.mkdir()
try:
    target = root / relative
    target.parent.mkdir(parents=True)
    target.write_text(original, encoding='utf-8')
    subprocess.run([sys.executable, str(local / 'prepare-ui.py'), str(root)], check=True)
    installed = target.read_text(encoding='utf-8')
    includes = '<link rel="stylesheet" href="/wr-device-homepage.css">\n'
    includes += ''.join('<script src="/wr-device-' + name + '.js"></script>\n' for name in assets)
    section = '\n                <section id="wr-connected-devices" class="well" aria-label="Connected devices"></section>'
    section += '\n                <section id="wr-roaming-history" class="well" aria-label="Wi-Fi history"></section>'
    assert installed.count(includes) == 1 and installed.count(section) == 1
    assert installed.replace(includes, '', 1).replace(section, '', 1) == original
    for name in assets:
        assert (target.parent / ('wr-device-' + name + '.js')).read_bytes() == (local / (name + '.js')).read_bytes()
    assert (target.parent / 'wr-device-homepage.css').read_bytes() == (local / 'homepage.css').read_bytes()
    before = target.read_bytes()
    repeated = subprocess.run([sys.executable, str(local / 'prepare-ui.py'), str(root)], capture_output=True)
    assert repeated.returncode != 0 and target.read_bytes() == before
finally:
    assert root.resolve().parent == Path.cwd().resolve()
    shutil.rmtree(root)
print('PASS actual homepage preserved, assets installed in dependency order, duplicate preparation rejected')
print('PASS UTF-8 homepage and pinned JS/CSS delivery routes; raw asset bytes:', asset_bytes)
