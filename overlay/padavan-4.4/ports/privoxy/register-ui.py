#!/usr/bin/env python3
"""Register candidate Privoxy capability and page."""
import argparse
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('trunk', type=Path)
args = parser.parse_args()
assets = Path(__file__).resolve().parent
edits = {}
web = args.trunk / 'user/httpd/web_ex.c'
s = web.read_text(encoding='utf-8')
if 'found_app_privoxy' in s:
    raise SystemExit('Privoxy capability already registered')
start = s.index('ej_firmware_caps_hook(')
end = s.index('\nstatic ', start)
segment = s[start:end]
anchor = '\treturn 0;\n}'
if segment.count(anchor) != 1:
    raise SystemExit('Inspect capability return')
segment = segment.replace(anchor,
    '#if defined(APP_PRIVOXY)\n\twebsWrite(wp, "function found_app_privoxy() { return 1; }\\n");\n'
    '#else\n\twebsWrite(wp, "function found_app_privoxy() { return 0; }\\n");\n#endif\n' + anchor, 1)
edits[web] = s[:start] + segment + s[end:]
www = args.trunk / 'user/www/Makefile'
s = www.read_text(encoding='utf-8')
if s.count('clean:\n') != 1 or 'Advanced_Services_Privoxy.asp' in s:
    raise SystemExit('Inspect www packaging')
edits[www] = s.replace('clean:\n', 'ifneq ($(CONFIG_FIRMWARE_INCLUDE_PRIVOXY),y)\n\trm -f $(INSTALLDIR)/www/Advanced_Services_Privoxy.asp\nendif\nclean:\n', 1)
page = args.trunk / 'user/www/n56u_ribbon_fixed/Advanced_Services_Privoxy.asp'
source = assets / 'Advanced_Services_Privoxy.asp'
if page.exists() or not source.is_file():
    raise SystemExit('Inspect page destination/source')
for filename, language in (('EN.footer', 'EN-privoxy.footer'),
                           ('UK.dict', 'UK-privoxy.dict'),
                           ('RU.dict', 'RU-privoxy.dict')):
    dictionary = args.trunk / 'user/www/dict' / filename
    text = dictionary.read_text(encoding='utf-8')
    keys = {line.split('=', 1)[0] for line in text.splitlines() if '=' in line}
    additions = [line for line in (assets / language).read_text(encoding='utf-8').splitlines()
                 if line.split('=', 1)[0] not in keys]
    edits[dictionary] = text.rstrip() + '\n' + '\n'.join(additions) + '\n'
for path, text in edits.items():
    path.write_text(text, encoding='utf-8')
shutil.copyfile(source, page)
print('Privoxy WebUI registered; browser and localization checks pending')
