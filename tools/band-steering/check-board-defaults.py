#!/usr/bin/env python3
"""Source fixtures for board selection and factory OFF; no device operation."""
import argparse
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('board_config', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
board = a.board_config.read_bytes()
defaults = (a.source / 'trunk/user/shared/defaults.c').read_bytes()
script = Path(__file__).with_name('prepare-board-defaults.py').resolve()
cases = [('valid', board, defaults, True)]
for name, old, new in (
    ('dtb', b'CONFIG_RALINK_BUILTIN_DTB_NAME="wr1200js"', b'CONFIG_RALINK_BUILTIN_DTB_NAME="other"'),
    ('chip2', b'CONFIG_FIRST_IF_MT7603E=y', b'CONFIG_FIRST_IF_MT7615=y'),
    ('chip5', b'CONFIG_RT_SECOND_IF_MT7612E=y', b'CONFIG_RT_SECOND_IF_MT7915=y'),
    ('module2', b'CONFIG_MT76X3_AP=m', b'CONFIG_MT76X3_AP=y'),
    ('module5', b'CONFIG_MT76X2_AP=m', b'CONFIG_MT76X2_AP=y'),
    ('selector', b'# CONFIG_RT_BAND_STEERING is not set', b'CONFIG_RT_BAND_STEERING=y'),
):
    if board.count(old) != 1:
        raise ValueError('Fixture board anchor changed: '+name)
    cases.append((name, board.replace(old, new), defaults, False))
for key in ('wl_band_steering', 'rt_band_steering'):
    old = ('{ "'+key+'", "0" }').encode()
    if defaults.count(old) != 1:
        raise ValueError('Fixture default anchor changed: '+key)
    cases.append((key+'-on', board, defaults.replace(old, old.replace(b'"0"', b'"1"')), False))
a.output.mkdir(parents=True, exist_ok=False)
for name, b, d, success in cases:
    root = a.output / name
    bp = root / 'trunk/configs/boards/WR1200JS/kernel-4.4.x.config'
    dp = root / 'trunk/user/shared/defaults.c'
    bp.parent.mkdir(parents=True); dp.parent.mkdir(parents=True)
    bp.write_bytes(b); dp.write_bytes(d)
    result = subprocess.run([sys.executable, str(script), str(root)], capture_output=True, text=True)
    if success:
        if result.returncode:
            raise AssertionError(result.stderr)
        bt, dt = bp.read_text(encoding='utf-8'), dp.read_text(encoding='utf-8')
        expected = b.decode().replace('# CONFIG_MT7603E_BAND_STEERING_7603 is not set',
                                     'CONFIG_MT7603E_BAND_STEERING_7603=y').replace(
                                     '# CONFIG_RT_BAND_STEERING is not set', 'CONFIG_RT_BAND_STEERING=y')
        assert bt.splitlines() == expected.splitlines()
        assert all('{ "'+k+'", "0" }' in dt for k in ('wr_bs_enable','wl_band_steering','rt_band_steering'))
        prepared = bp.read_bytes(), dp.read_bytes()
        again = subprocess.run([sys.executable, str(script), str(root)], capture_output=True)
        assert again.returncode and prepared == (bp.read_bytes(), dp.read_bytes())
    else:
        assert result.returncode and bp.read_bytes() == b and dp.read_bytes() == d
        assert not (root / 'band-steering-board-defaults.json').exists()
    print(name+': PASS')
assert a.board_config.read_bytes() == board
assert (a.source / 'trunk/user/shared/defaults.c').read_bytes() == defaults
