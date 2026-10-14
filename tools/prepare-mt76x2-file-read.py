#!/usr/bin/env python3
"""Guard invalid vendor file handles before either kernel read path.

Reference: xiaobei207/padavan-4.4-2@5e48032, MT76x2 rt_linux.c.
Our adaptation also rejects ERR_PTR handles and covers the legacy branch.
"""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
args = parser.parse_args()
path = args.source / 'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x2/os/linux/rt_linux.c'
text = path.read_text(encoding='utf-8')
anchor = 'int RtmpOSFileRead(RTMP_OS_FD osfd, char *pDataPtr, int readLen)\n{\n'
if text.count(anchor) != 1 or 'wr_mt76x2_file_read_guard' in text:
    raise SystemExit('MT76x2 file-read anchor changed or already patched')
replacement = '#include <linux/err.h>\n' + anchor + '''
	/* wr_mt76x2_file_read_guard: reject failed opens before dereferencing. */
	if (IS_ERR_OR_NULL(osfd))
		return -1;
'''
path.write_text(text.replace(anchor, replacement), encoding='utf-8')
print('Prepared MT76x2 invalid file-handle guard; runtime unverified')
