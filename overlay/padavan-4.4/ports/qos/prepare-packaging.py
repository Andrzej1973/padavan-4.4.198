#!/usr/bin/env python3
"""Install the already-built iproute2 tc when QoS or SQM is selected."""
import argparse
from pathlib import Path

OLD = ('ifeq ($(CONFIG_FIRMWARE_INCLUDE_SQM),y)\n'
       '\t$(ROMFSINST) $(THISDIR)/$(SRC_NAME)/tc/tc /bin/tc\nendif')
NEW = ('# WR QoS: tc is required independently of the optional SQM service.\n'
       'ifneq ($(filter y,$(CONFIG_FIRMWARE_INCLUDE_QOS) $(CONFIG_FIRMWARE_INCLUDE_SQM)),)\n'
       '\t$(ROMFSINST) $(THISDIR)/$(SRC_NAME)/tc/tc /bin/tc\nendif')


def prepare(text):
    if text.count(NEW) == 1 and OLD not in text:
        return text
    if text.count(OLD) != 1 or '# WR QoS:' in text:
        raise ValueError('Unexpected pinned iproute2 tc packaging rules')
    return text.replace(OLD, NEW, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', type=Path)
    args = parser.parse_args()
    path = args.target / 'trunk/user/iproute2/Makefile'
    path.write_text(prepare(path.read_text(encoding='utf-8')), encoding='utf-8')
    print('Prepared /bin/tc packaging for QoS or SQM; no service or kernel option enabled')


if __name__ == '__main__':
    main()
