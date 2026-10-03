#!/usr/bin/env python3
"""Prepare pinned ZeroTier 1.16.2 for deterministic Padavan cross-compilation."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
args = parser.parse_args()
path = args.source / 'make-linux.mk'
text = path.read_text(encoding='utf-8')
changes = [
    ('ifeq ($(wildcard /usr/include/natpmp.h),)',
     '# Padavan cross-build: always use bundled target NAT-PMP.\nifeq (0,0)'),
    ('ext/${OTEL_INSTALL_DIR}/include/opentelemetry/version.h',
     '${OTEL_INSTALL_DIR}/include/opentelemetry/version.h'),
]
for old, new in changes:
    count = text.count(old)
    expected = 2 if old.startswith('ext/${OTEL') else 1
    if count != expected:
        raise SystemExit('Unexpected pinned source for %r: %d matches, expected %d' % (old, count, expected))
    text = text.replace(old, new)
# miniupnpc is controlled explicitly by the build invocation:
# MINIUPNPC_IS_NEW_ENOUGH=0. Do not detect host target libraries.
with path.open('w', encoding='utf-8', newline='\n') as output:
    output.write(text)
print('Prepared bundled NAT-PMP and OpenTelemetry header dependency paths.')


