#!/usr/bin/env python3
"""Replace the pinned ZeroTier prebuilt recipe with the verified source recipe."""
import argparse
from pathlib import Path
import shutil
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('--prepare-script',required=True,type=Path)
a=p.parse_args()
directory=a.source/'trunk/user/zerotier'
recipe=directory/'Makefile'
text=recipe.read_text(encoding='utf-8')
if 'SRC_NAME = ZeroTierOne-1.14.0' not in text:
    raise SystemExit('Unexpected pinned ZeroTier recipe; refusing replacement')
helper=a.prepare_script.resolve(strict=True)
shutil.copyfile(Path(__file__).with_name('Makefile'),recipe)
shutil.copyfile(helper,directory/'prepare-source.py')
print('ZeroTier 1.16.2 source recipe installed; target libatomic packaging enabled.')

