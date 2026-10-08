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
p.add_argument('--preprocessor', help='Host C preprocessor for actual MT7612/MT7603 conditionals')
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
        # The coordinated default must precede conditional radio entries.
        array_start = dt.index('struct nvram_pair router_defaults[] = {')
        coordinated = dt.index('{ "wr_bs_enable", "0" }')
        assert array_start < coordinated < dt.index('#if', array_start)
        if a.preprocessor:
            headers = root / 'preprocessor-headers'
            headers.mkdir()
            for header in ('ralink_boards.h','nvram_linux.h','netutils.h','defaults.h'):
                (headers/header).write_text('/* Isolated preprocessing fixture. */\n')
            pp = subprocess.run([a.preprocessor, '-E', '-P', '-I'+str(headers),
                                 '-DUSE_WID_5G=7612', '-DUSE_WID_2G=7603',
                                 str(dp)], capture_output=True, text=True, check=True)
            assert pp.stdout.count('{ "wr_bs_enable", "0" }') == 1
            (root/'defaults-mt7612-preprocessed.c').write_text(pp.stdout)
            # Prove this gate catches the previous erroneous insertion.
            old = dt.replace('\t{ "wr_bs_enable", "0" }, /* coordinated WR steering: factory OFF */\n','')
            old = old.replace('\t{ "wl_band_steering", "0" },',
                              '\t{ "wr_bs_enable", "0" },\n\t{ "wl_band_steering", "0" },')
            previous = dp.with_name('previous-conditional-default.c')
            previous.write_text(old)
            pp_old = subprocess.run([a.preprocessor, '-E', '-P', '-I'+str(headers),
                                     '-DUSE_WID_5G=7612', '-DUSE_WID_2G=7603',
                                     str(previous)], capture_output=True, text=True, check=True)
            assert 'wr_bs_enable' not in pp_old.stdout
            print('Actual MT7612/MT7603 preprocessing and previous-bug rejection: PASS')
        prepared = bp.read_bytes(), dp.read_bytes()
        again = subprocess.run([sys.executable, str(script), str(root)], capture_output=True)
        assert again.returncode and prepared == (bp.read_bytes(), dp.read_bytes())
    else:
        assert result.returncode and bp.read_bytes() == b and dp.read_bytes() == d
        assert not (root / 'band-steering-board-defaults.json').exists()
    print(name+': PASS')
assert a.board_config.read_bytes() == board
assert (a.source / 'trunk/user/shared/defaults.c').read_bytes() == defaults
