#!/usr/bin/env python3
"""Install candidate sources into an isolated pinned 4.4 kernel, default off."""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kernel', type=Path)
    parser.add_argument('candidate', type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    kernel = args.kernel.resolve()
    candidate = args.candidate.resolve()
    if kernel == candidate or candidate in kernel.parents or kernel in candidate.parents:
        parser.error('Kernel and driver candidate must be separate trees')
    version = (kernel / 'Makefile').read_text(encoding='utf-8')
    for key, value in [('VERSION', '4'), ('PATCHLEVEL', '4'), ('SUBLEVEL', '198')]:
        if not re.search(r'^' + key + r'\s*=\s*' + value + r'\s*$', version, re.M):
            parser.error('Expected kernel 4.4.198')
    parent = kernel / 'drivers/net/wireless/mediatek'
    destination = parent / 'mi-mini'
    if destination.exists():
        parser.error('Candidate driver directory already exists')
    updates = []
    for filename, addition in [
        ('Makefile', 'obj-$(CONFIG_MI_MINI_RADIO) += mi-mini/'),
        ('Kconfig', 'source "drivers/net/wireless/mediatek/mi-mini/Kconfig"'),
    ]:
        target = parent / filename
        reference = here / 'mi-mini-donors/kernel-4.4' / ('mediatek.' + filename)
        content = target.read_text(encoding='utf-8')
        if content != reference.read_text(encoding='utf-8'):
            parser.error('Parent driver file differs from pinned reference: ' + filename)
        updates.append((target, content + '\n' + addition + '\n'))
    if not (candidate / 'os/linux/mi_mini_platform.c').is_file():
        parser.error('Platform adapter missing')
    if 'default n' not in (candidate / 'Kconfig').read_text(encoding='utf-8'):
        parser.error('Candidate must remain default off')
    if any(path.is_symlink() for path in candidate.rglob('*')):
        parser.error('Symlinks are unsupported in candidate source')
    # This helper validates the existing bridge before making its first write.
    subprocess.run([
        sys.executable, str(here / 'integrate-mi-mini-factory.py'), str(kernel),
        str(candidate / 'os/linux/mi_mini_factory.c'),
        str(here / 'mi-mini-donors/kernel-4.4/mt_wifi_mtd.c'),
    ], check=True)
    shutil.copytree(str(candidate), str(destination))
    for target, content in updates:
        target.write_text(content, encoding='utf-8')
    print('Installed default-off MI-MINI radio candidate:', destination)
    print('Kernel configuration and DTS unchanged; not a bootable board port.')


if __name__ == '__main__':
    main()
