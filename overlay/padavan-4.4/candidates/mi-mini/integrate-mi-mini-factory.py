#!/usr/bin/env python3
"""Add the checked Factory API to an isolated vendor 4.4 kernel candidate."""
import argparse
import hashlib
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('kernel', type=Path)
    parser.add_argument('helper', type=Path)
    parser.add_argument('reference', type=Path,
                        help='Pinned wifi_utility/mt_wifi_mtd.c reference')
    args = parser.parse_args()
    target = args.kernel / 'drivers/net/wireless/wifi_utility/mt_wifi_mtd.c'
    makefile = target.parent / 'Makefile'
    source = target.read_bytes()
    reference = args.reference.read_bytes()
    # Permit LF/CRLF host differences while retaining exact source text.
    canonical = lambda data: data.replace(b'\r\n', b'\n')
    if canonical(source) != canonical(reference):
        parser.error('Target MTD bridge differs from the pinned reference')
    build = makefile.read_text(encoding='utf-8')
    if 'wifi_utility-objs := mt_wifi_mtd.o pci_mediatek_rbus.o' not in build:
        parser.error('Unsupported wifi_utility build layout')
    helper = args.helper.read_text(encoding='utf-8')
    if (helper.count('int mi_mini_factory_read(') != 1 or
            helper.count('int mi_mini_factory_write(') != 1 or 'EXPORT_SYMBOL' in helper):
        parser.error('Unexpected adapter definition')
    if 'mt_mtd_write_nm_wifi' not in source.decode('utf-8'):
        parser.error('Original MTD APIs missing')
    appended = ('\n/* Isolated MI-MINI Factory adapter, selected only for MT7620. */\n'
                '#ifdef CONFIG_SOC_MT7620\n' + helper +
                '\nEXPORT_SYMBOL(mi_mini_factory_read);\n'
                'EXPORT_SYMBOL(mi_mini_factory_write);\n'
                '#endif /* CONFIG_SOC_MT7620 */\n')
    target.write_bytes(canonical(source) + appended.encode('utf-8'))
    print('Appended checked Factory API to isolated kernel bridge')
    print('Pinned bridge SHA256:', hashlib.sha256(canonical(reference)).hexdigest())
    print('Original MTD functions preserved; no radio or board enabled.')


if __name__ == '__main__':
    main()
