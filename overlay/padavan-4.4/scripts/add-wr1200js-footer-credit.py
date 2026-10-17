#!/usr/bin/env python3
"""Add a localized, narrowly scoped credit for WR1200JS port adaptations."""
import argparse
from pathlib import Path
import re


parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('--verify-image', action='store_true')
args = parser.parse_args()

CREDIT_KEY = 'WR1200JS_Credit'
CREDITS = {
    'EN.footer': 'WR1200JS firmware adaptations by Andrzej1973',
    'UK.dict': 'Адаптації прошивки WR1200JS: Andrzej1973',
    'RU.dict': 'Адаптации прошивки WR1200JS: Andrzej1973',
}
UPSTREAM_NAMES = (
    'Andy Padavan', 'hanwckf', 'MeIsReallyBa', 'tsl0922', 'TurBoTse', 'vipshmily'
)
NOTICE = 'Firmware distribution is prohibited , Non-Commercial Use Only'
FOOTER_LINE = re.compile(
    r"(?m)^(?P<indent>[\t ]*)footer_code \+='  <span>Developed by © .*?</span></br>\\n';$"
)


def read(path):
    return path.read_text(encoding='utf-8')


def dictionary_value(path):
    matches = [line.split('=', 1)[1] for line in read(path).splitlines()
               if line.startswith(CREDIT_KEY + '=')]
    if len(matches) != 1:
        raise SystemExit('Expected exactly one ' + CREDIT_KEY + ' entry in ' + str(path))
    return matches[0]


if args.verify_image:
    root = args.source / 'trunk/romfs/www'
    state = read(root / 'state.js')
    if state.count('<#' + CREDIT_KEY + '#>') != 1:
        raise SystemExit('Localized WR1200JS footer credit missing or duplicated in image')
    upstream_line = next((line for line in state.splitlines()
                          if 'Developed by ©' in line and 'vipshmily' in line), '')
    if not upstream_line or any(name not in upstream_line for name in UPSTREAM_NAMES):
        raise SystemExit('Original upstream developer credits changed or missing')
    notice_line = next((line for line in state.splitlines() if NOTICE in line), '')
    if not notice_line:
        raise SystemExit('Original firmware distribution notice missing')
    image_dictionaries = {'EN.footer': 'EN.dict', 'UK.dict': 'UK.dict', 'RU.dict': 'RU.dict'}
    for source_name, expected in CREDITS.items():
        image_name = image_dictionaries[source_name]
        if dictionary_value(root / image_name) != expected:
            raise SystemExit('Missing or incorrect localized credit in ' + image_name)
    print('PASS WR1200JS attribution, upstream credits and distribution notice in image')
    raise SystemExit(0)


www = args.source / 'trunk/user/www'
state_path = www / 'n56u_ribbon_fixed/state.js'
state = read(state_path)
if CREDIT_KEY in state:
    raise SystemExit('WR1200JS attribution already exists; refusing duplicate insertion')
matches = list(FOOTER_LINE.finditer(state))
if len(matches) != 1:
    raise SystemExit('Could not uniquely identify upstream developer credit line')
upstream_line = matches[0].group(0)
if any(name not in upstream_line for name in UPSTREAM_NAMES):
    raise SystemExit('Upstream developer credit line differs from the reviewed source')
notice_line = next((line for line in state.splitlines() if NOTICE in line), '')
if not notice_line:
    raise SystemExit('Original distribution notice is missing; no files written')

changes = []
indent = matches[0].group('indent')
credit_line = indent + "footer_code +='  <span><#" + CREDIT_KEY + "#></span></br>\\n';"
state = state[:matches[0].end()] + '\n' + credit_line + state[matches[0].end():]
changes.append((state_path, state))

for name, value in CREDITS.items():
    path = www / 'dict' / name
    dictionary = read(path)
    if any(line.startswith(CREDIT_KEY + '=') for line in dictionary.splitlines()):
        raise SystemExit('Translation key already exists in ' + str(path) + '; no files written')
    changes.append((path, dictionary.rstrip('\n') + '\n' + CREDIT_KEY + '=' + value + '\n'))

for path, content in changes:
    path.write_text(content, encoding='utf-8', newline='\n')
print('Added localized WR1200JS port attribution while preserving upstream footer credits')
