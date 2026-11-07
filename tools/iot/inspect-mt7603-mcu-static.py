#!/usr/bin/env python3
"""Bounded static E2 decoding; never execute firmware or claim ACK semantics.

Requires optional pypcode with NDS32 language data. Run with an isolated
PYTHONPATH if that dependency is not installed. Output is JSON on stdout.
Offsets below are hypotheses tied to an exact image SHA256, not generic ABI.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import pypcode

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('driver', type=Path)
a = p.parse_args()
header = a.driver / 'include/mcu/mt7603_e2_firmware.h'
raw = header.read_bytes()
text = re.sub(r'/\*.*?\*/|//[^\n]*', '', raw.decode(), flags=re.S)
arrays = re.findall(r'\bUCHAR\s+MT7603_e2_FirmwareImage\s*\[\s*\]\s*=\s*\{([^}]*)\}', text)
if len(arrays) != 1:
    p.error('Expected one E2 initializer')
tokens = arrays[0].strip().rstrip(',').split(',')
if not all(re.fullmatch(r'\s*0[xX][0-9a-fA-F]{2}\s*', x) for x in tokens):
    p.error('Unsupported initializer')
image = bytes(int(x, 16) for x in tokens)
identity = hashlib.sha256(image).hexdigest()
if identity != 'e897b5ca7277d77778dda75450956143709e39005affaf2b682c1e7d79fc4c64':
    p.error('Offsets reviewed only for pinned CL173766_R E2 image')
base = 0x100000
sdk = (a.driver / 'include/mcu/andes_mt.h').read_text()
if not re.search(r'#define\s+FW_CODE_START_ADDRESS1\s+0x100000\b', sdk):
    p.error('Changed load-base definition')
payload_end = base + int.from_bytes(image[-4:], 'little') + 4
context = pypcode.Context('NDS32:BE:32:default')
blocks = []
for offset, count in [(0, 3), (0x230, 85), (0x11f70, 9), (0xd0, 12)]:
    data = image[offset:offset + 512]
    decoded = context.disassemble(data, base_address=base + offset,
                                  max_instructions=count)
    blocks.append({'file_offset': offset, 'instructions': [
        {'address': i.addr.offset, 'length': i.length,
         'mnemonic': i.mnem, 'operands': i.body}
        for i in decoded.instructions]})
# addi.gp operands are blank in this language's assembly rendering. Preserve
# actual lifted operations, rather than guessing operands from that rendering.
lifted = {}
for offset in [0x11f74, 0x11f78, 0x2bc, 0x2e8]:
    lifted[hex(base + offset)] = [str(op) for op in context.translate(
        image[offset:offset + 16], base_address=base + offset,
        max_instructions=1).ops]
gp_candidate = payload_end + 0x4cc4
assert gp_candidate == 0x116f24
log_address = gp_candidate - 0x6764
log_offset = log_address - base
log = image[log_offset:].split(b'\0', 1)[0].decode('ascii')
assert log == 'REG32(SYS_TOP_MISC2) = 0x%x \n'
assert gp_candidate - 0x16e54 == base + 0xd0
assert gp_candidate - 0x4cc4 == payload_end
print(json.dumps({
    'image_sha256': identity, 'header_sha256': hashlib.sha256(raw).hexdigest(),
    'load_base': base, 'payload_end': payload_end, 'blocks': blocks,
    'gp_related_pcode': lifted,
    'gp_candidate': gp_candidate,
    'corroboration': {'startup_log_address': log_address, 'startup_log': log,
                      'dispatch_candidate': base + 0xd0,
                      'zero_loop_begin_candidate': payload_end,
                      'zero_loop_end_candidate': gp_candidate - 0x3734},
    'limits': 'GP inferred by equating zero-loop start with payload end; '
              'log and function-start matches corroborate, not prove it. '
              'No instruction execution, complete CFG, relocation or ROM '
              'resolution; decoder needs independent confirmation.',
    'firmware_ack_contract_verified': False, 'runtime_verified': False,
}, indent=2))
