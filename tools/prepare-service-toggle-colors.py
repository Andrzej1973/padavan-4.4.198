#!/usr/bin/env python3
"""Color enabled iToggle controls green; retain existing OFF/loading artwork."""
import argparse
from pathlib import Path

STYLE = '''
/* WR enabled-toggle palette: preserve the existing sprite and switch behavior. */
div.main_itoggle label.itoggle.iTon:not(.disabled) {
    -webkit-filter: hue-rotate(-75deg) saturate(1.15);
    filter: hue-rotate(-75deg) saturate(1.15);
}
'''
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('tree', type=Path)
p.add_argument('--verify-image', action='store_true')
a = p.parse_args()
www = a.tree / ('trunk/romfs/www' if a.verify_image else 'trunk/user/www/n56u_ribbon_fixed')
css = www / 'bootstrap/css/engage.itoggle.css'
text = css.read_text(encoding='utf-8')
if a.verify_image:
    if text.count(STYLE.strip()) != 1:
        raise SystemExit('Enabled-toggle palette missing or duplicated in ROMFS')
    print('PASS enabled toggles green, existing OFF/loading artwork retained')
else:
    if 'WR enabled-toggle palette' in text:
        raise SystemExit('Enabled-toggle palette already installed')
    if 'div.main_itoggle label.itoggle' not in text or 'itoggle.png' not in text:
        raise SystemExit('Base iToggle stylesheet changed')
    css.write_text(text.rstrip() + '\n' + STYLE, encoding='utf-8', newline='\n')
    print('Prepared shared green ON toggle palette; no setting or runtime behavior changed')
