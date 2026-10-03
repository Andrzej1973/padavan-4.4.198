#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
import shutil

p = argparse.ArgumentParser()
p.add_argument('target', type=Path)
a = p.parse_args()
assets = Path(__file__).parent
www = a.target / 'trunk/user/www'
page = www / 'n56u_ribbon_fixed/Advanced_SQM.asp'
defaults = a.target / 'trunk/user/shared/defaults.c'
labels = json.loads((assets / 'web-labels.json').read_text(encoding='utf-8'))
if not page.is_file() or 'value="SqmConf;"' not in page.read_text(encoding='utf-8'):
    raise SystemExit('Existing SQM page contract requires review')
if '{ "sqm_enable", "0" }' not in defaults.read_text(encoding='utf-8'):
    raise SystemExit('SQM must remain disabled by default')
updates = []
for lang, values in labels.items():
    path = www / 'dict' / ('EN.footer' if lang == 'EN' else lang + '.dict')
    content = path.read_text(encoding='utf-8')
    if any(key + '=' in content for key in values):
        raise SystemExit('CAKE labels already present: ' + lang)
    updates.append((path, content.rstrip() + '\n' +
                    '\n'.join(key + '=' + value for key, value in values.items()) + '\n'))
for path, content in updates:
    path.write_text(content, encoding='utf-8')
shutil.copyfile(assets / 'Advanced_SQM.asp', page)
print('CAKE page prepared; default remains off; packaging and router checks pending')
