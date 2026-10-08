#!/usr/bin/env python3
"""Register the package in Padavan userspace with an explicit build selector.

Requires a layout generated from the matching prepared driver tree. This script
does not enable the selector, prepare drivers/rc, add runtime defaults or start
the service. Call only as part of the complete source integration sequence.
"""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--layout', type=Path, required=True)
a = p.parse_args()
user = a.source / 'trunk/user'
makefile = user / 'Makefile'
text = makefile.read_text()
anchor = 'all: $(patsubst %,%_only,$(dir_y))\n'
destination = user / 'wr-band-steering'
if text.count(anchor) != 1 or destination.exists() or 'wr-band-steering' in text:
    raise ValueError('Package registration anchors changed; no files written')
layout = a.layout.read_bytes()
if b'WR_BAND' not in layout or b'#define' not in layout:
    raise ValueError('Missing generated driver layout; no files written')
tools = Path(__file__).parent
recipe = (tools / 'package/Makefile').read_text()
# Resolve all inputs before any source mutation.
modules = ('protocol session clients aging policy grants coordinator loop '
           'events framing listener transport control main ctl control-client').split()
files = {name+'.c': (tools / (name+'.c')).read_bytes() for name in modules}
files.update({f.name: f.read_bytes() for f in tools.glob('*.h')})
files['protocol-layout.h'] = layout
files['package.mk'] = recipe.encode('utf-8')
files['Makefile'] = ("SOURCE_DIR = .\nLAYOUT_DIR = .\nBUILD_DIR = build\n"
                     "include package.mk\n").encode('utf-8')
registration = 'dir_$(CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING) += wr-band-steering\n\n'
destination.mkdir()
for name, data in files.items():
    (destination / name).write_bytes(data)
makefile.write_text(text.replace(anchor, registration + anchor))
print('Registered WR Band Steering package; selector and runtime state unchanged')
