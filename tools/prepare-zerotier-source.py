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
# Both addRoute and delRoute append RTA_SRC but omit it from nlmsg_len.
# IPv4/IPv6 payload lengths are 8/20 bytes including rtattr, already aligned.
# Preserve route selection semantics and account for the complete attribute.
netlink_path = args.source / 'osdep' / 'LinuxNetLink.cpp'
netlink = netlink_path.read_text(encoding='utf-8')
old = '\t\treq.rt.rtm_src_len = src.netmaskBits();\n'
if netlink.count(old) != 2:
    raise SystemExit('Unexpected pinned RTA_SRC accounting source')
netlink = netlink.replace(old, old + '\t\trtl += rtap->rta_len;\n')
with netlink_path.open('w', encoding='utf-8', newline='\n') as output:
    output.write(netlink)
# uClibc toolchain does not expose C99 round in std:: (CI 37152606135).
# Retain inja's rounding feature through the available C-library function.
inja_path = args.source / 'ext' / 'inja' / 'inja.hpp'
inja = inja_path.read_text(encoding='utf-8')
if inja.count('std::round(') != 1:
    raise SystemExit('Unexpected pinned inja rounding implementation')
inja = inja.replace('std::round(', '::round(')
with inja_path.open('w', encoding='utf-8', newline='\n') as output:
    output.write(inja)
with path.open('w', encoding='utf-8', newline='\n') as output:
    output.write(text)
print('Prepared bundled NAT-PMP, OpenTelemetry dependencies and RTA_SRC length accounting.')


