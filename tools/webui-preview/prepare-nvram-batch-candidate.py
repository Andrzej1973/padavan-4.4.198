#!/usr/bin/env python3
"""Compose an uninstalled NVRAM batch/commit-order target candidate; no ioctl."""
import argparse
import importlib.util
from pathlib import Path

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('commit_order', here / 'prepare-nvram-commit-order.py')
commit_order = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commit_order)

def transform(source):
    if 'wr_nvram_batch_candidate' in source:
        raise ValueError('NVRAM batch candidate already present')
    source = commit_order.transform(source)
    marker = '_nvram_free(struct nvram_tuple *t)\n{'
    if source.count(marker) != 1:
        raise ValueError('NVRAM allocator free anchor changed')
    start = source.index(marker)
    end = source.index('\n}', start) + 2
    core = (here / 'nvram-batch-core.c.inc').read_text()
    signature = 'static int wr_nvram_batch_candidate('
    if core.count(signature) != 1:
        raise ValueError('NVRAM batch core signature changed')
    # An externally visible but unexported, uncalled symbol ensures the object
    # actually contains compiled batch code. No userspace API is installed.
    core = core.replace(signature, 'int wr_nvram_batch_candidate(', 1)
    wire_header = (here / 'nvram-batch-wire.h').read_text()
    wire_decoder = (here / 'nvram-batch-wire.c.inc').read_text()
    user_entry = (here / 'nvram-batch-user.c.inc').read_text()
    return '#include <linux/capability.h>\n#include <linux/uaccess.h>\n' + source[:end] + '\n\n' + core + '\n' + wire_header + '\n' + wire_decoder + '\n' + user_entry + source[end:]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    target = args.source / 'trunk/linux-4.4.x/drivers/nvram/nvram_linux.c'
    target.write_text(transform(target.read_text()))
    print('Prepared isolated batch/commit-order candidate; no ioctl/export/installation')
