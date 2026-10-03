#!/usr/bin/env python3
"""Add the pinned source OpenSSL 3.5 build without dropping the vendor fallback."""
import argparse
from pathlib import Path
import shutil

p = argparse.ArgumentParser()
p.add_argument('target', type=Path)
p.add_argument('source', type=Path)
a = p.parse_args()
target = a.target / 'trunk/libs/libssl'
source = a.source / 'trunk/libs/libssl/3.5'
make = target / 'Makefile'
template = a.target / 'trunk/configs/templates/WR1200JS.config'
old = make.read_text()
if not old.startswith('SRC_NAME=openssl-1.1.1w\n'):
    raise SystemExit('Unexpected vendor OpenSSL build; refusing to overwrite')
new = (source / 'Makefile').read_text()
atomic = '\tcp -fP $(CONFIG_CROSS_COMPILER_ROOT)/mipsel-linux-uclibc/sysroot/lib/libatomic.so* $(ROMFSDIR)/lib'
if new.count(atomic) != 1:
    raise SystemExit('Unexpected source libatomic installation')
new = new.replace(atomic, '\tatomic_lib="$$($(CROSS_COMPILE)gcc -print-file-name=libatomic.so.1)"; \\\n\t  test -f "$$atomic_lib" && cp -fL "$$atomic_lib" $(ROMFSDIR)/lib/libatomic.so.1')
if not (source / 'patches').is_dir() or not (source / 'openssl.cnf').is_file():
    raise SystemExit('Missing pinned OpenSSL patches or configuration')
if (target / '3.5').exists():
    raise SystemExit('OpenSSL 3.5 destination already exists')
config = template.read_text()
for key in ('CONFIG_FIRMWARE_INCLUDE_OPENSSL_35', 'CONFIG_FIRMWARE_INCLUDE_QUIC'):
    if key not in config:
        config += '\n' + key + '=n\n'
shutil.copytree(source, target / '3.5')
(target / '3.5/Makefile').write_text(new)
dispatch = '''# Preserve the vendor 1.1.1 build when neither new selector is requested.
ifneq (,$(filter y,$(CONFIG_FIRMWARE_INCLUDE_OPENSSL_35) $(CONFIG_FIRMWARE_INCLUDE_QUIC)))
.PHONY: all install romfs clean
all install romfs clean:
\t$(MAKE) -C 3.5 $@
else
'''
make.write_text(dispatch + old + '\nendif\n')
template.write_text(config)
print('OpenSSL 3.5 selector and build installed; QUIC curl integration remains separate')
