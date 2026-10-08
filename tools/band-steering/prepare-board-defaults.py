#!/usr/bin/env python3
"""Prepare WR1200JS build support and explicit factory-OFF service defaults.

Run only in the complete steering integration sequence, before kernel config
generation. This does not supply the driver patches, daemon, rc or WebUI.
"""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
root = p.parse_args().source
board = root / 'trunk/configs/boards/WR1200JS/kernel-4.4.x.config'
defaults = root / 'trunk/user/shared/defaults.c'
original_board, original_defaults = board.read_bytes(), defaults.read_bytes()
config, text = board.read_text(encoding='utf-8'), defaults.read_text(encoding='utf-8')
for required in ('CONFIG_RALINK_BUILTIN_DTB_NAME="wr1200js"',
                 'CONFIG_FIRST_IF_MT7603E=y', 'CONFIG_RT_SECOND_IF_MT7612E=y',
                 'CONFIG_MT76X3_AP=m', 'CONFIG_MT76X2_AP=m'):
    if config.splitlines().count(required) != 1:
        raise ValueError('WR1200JS board selection changed; no files written')
for symbol in ('MT7603E_BAND_STEERING_7603', 'RT_BAND_STEERING'):
    disabled = '# CONFIG_'+symbol+' is not set'
    if config.splitlines().count(disabled) != 1:
        raise ValueError('Expected disabled steering selector; no files written')
    config = config.replace(disabled, 'CONFIG_'+symbol+'=y')
anchor = '\t{ "wl_band_steering", "0" },'
if text.count(anchor) != 1 or text.count('{ "rt_band_steering", "0" }') != 1 or 'wr_bs_enable' in text:
    raise ValueError('Factory-OFF defaults changed; no files written')
array_anchor = 'struct nvram_pair router_defaults[] = {\n'
if text.count(array_anchor) != 1:
    raise ValueError('Defaults array anchor changed; no files written')
text = text.replace(array_anchor, array_anchor+
                    '\t{ "wr_bs_enable", "0" }, /* coordinated WR steering: factory OFF */\n')
board.write_text(config, encoding='utf-8')
defaults.write_text(text, encoding='utf-8')
report = {'runtime_verified': False, 'factory_enabled': False,
          'files': {str(path.relative_to(root)): {
              'before_sha256': hashlib.sha256(before).hexdigest(),
              'after_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
              for path, before in ((board, original_board), (defaults, original_defaults))}}
(root / 'band-steering-board-defaults.json').write_text(json.dumps(report, indent=2)+'\n')
print('Prepared WR steering build selectors and factory-OFF defaults')
