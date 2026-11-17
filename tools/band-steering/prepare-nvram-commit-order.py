"""Serialize native commit snapshot creation with its flash operation."""
import argparse
import hashlib
from pathlib import Path


def prepare(text):
    start = text.index('int\nnvram_commit(void)')
    end = text.index('\n}', start) + 2
    body = text[start:end]
    if hashlib.sha256(body.encode()).hexdigest() != 'f69702be1b26ac9e55278435cb52becfd0a74263e307fa1383b65b772d0b6bc1':
        raise ValueError('Pinned native commit changed; no files written')
    # The pinned file has no second nvram_sem consumer with inverse ordering.
    if text.count('mutex_lock(&nvram_sem);') != 1 or text.count('mutex_unlock(&nvram_sem);') != 1:
        raise ValueError('Native flash mutex consumers changed; no files written')
    body = body.replace('\tmutex_lock(&nvram_sem);\n\n', '', 1)
    body = body.replace('\t/* Regenerate NVRAM */',
                        '\t/* Serialize snapshot and flash in the same commit order. */\n'
                        '\tmutex_lock(&nvram_sem);\n\n\t/* Regenerate NVRAM */', 1)
    body = body.replace('\t\tgoto done;', '\t\tgoto skip_write;', 1)
    body = body.replace('\ndone:\n', '\n', 1)
    return text[:start] + body + text[end:]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    path = args.source / 'trunk/linux-4.4.x/drivers/nvram/nvram_linux.c'
    updated = prepare(path.read_text())
    path.write_text(updated)
    print('Native commit mutex covers snapshot plus flash; generation failures unlock without writing')
