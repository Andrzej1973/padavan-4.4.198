#!/usr/bin/env python3
"""Install the lightweight hybrid dashboard alongside Classic assets."""
import argparse
from pathlib import Path
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
args = parser.parse_args()
root = args.source.resolve(strict=True)
www = root / 'trunk/user/www'
makefile = www / 'Makefile'
classic = www / 'n56u_ribbon_fixed'
target = www / 'hybrid'
here = Path(__file__).resolve().parent
assets = ('index.html', 'dashboard.css', 'dashboard.js')
anchor = '\tcp -R $(WEBUI_NAME) $(ROMFS_DIR)/www\n'
copy = '\tcp -R hybrid $(ROMFS_DIR)/www/hybrid\n'
if not classic.is_dir() or not makefile.is_file():
    parser.error('Expected Padavan Classic web source tree')
text = makefile.read_text(encoding='utf-8')
if target.exists() or text.count(anchor) != 1 or copy in text:
    parser.error('Hybrid destination exists or ROMFS copy anchor changed')
if any(not (here / name).is_file() for name in assets):
    parser.error('Missing dashboard asset')
if sum((here / name).stat().st_size for name in assets) > 100_000:
    parser.error('Dashboard assets exceed 100 KB')
target.mkdir()
for name in assets:
    shutil.copyfile(here / name, target / name)
makefile.write_text(text.replace(anchor, anchor + copy, 1), encoding='utf-8')
print('Installed hybrid dashboard alongside Classic; image/runtime verification pending')
