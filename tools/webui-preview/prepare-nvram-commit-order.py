#!/usr/bin/env python3
"""Isolated candidate only: serialize NVRAM snapshot through flash completion."""
import argparse
from pathlib import Path

def transform(source):
    start = source.index('nvram_commit(void)\n{')
    end = source.index('\n}', start) + 2
    body = source[start:end]
    replacements = [
        ('\t/* Regenerate NVRAM */', '\t/* Serialize snapshot creation and flash persistence together. */\n\tmutex_lock(&nvram_sem);\n\n\t/* Regenerate NVRAM */'),
        ('\n\tmutex_lock(&nvram_sem);\n\n\t/* Check partition unchanged */', '\n\t/* Check partition unchanged */'),
        ('skip_write:\n\tmutex_unlock(&nvram_sem);\n\ndone:', 'skip_write:\ndone:\n\tmutex_unlock(&nvram_sem);'),
    ]
    for old, new in replacements:
        if body.count(old) != 1:
            raise ValueError('NVRAM commit anchor changed: ' + old)
        body = body.replace(old, new, 1)
    return source[:start] + body + source[end:]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    target = args.source / 'trunk/linux-4.4.x/drivers/nvram/nvram_linux.c'
    target.write_text(transform(target.read_text()))
    print('Prepared isolated NVRAM commit ordering candidate; target/runtime unverified')
