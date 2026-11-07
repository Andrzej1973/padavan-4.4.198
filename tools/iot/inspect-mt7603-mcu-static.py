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
import struct
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
for offset, count in [(0, 3), (0x230, 85), (0x11f70, 9), (0xd0, 88),
                      (0x3e0c, 37), (0x5ea4, 37), (0x775c, 28),
                      (0x6f90, 126), (0x71f8, 88), (0x6154, 37),
                      (0x433c, 31), (0x8da4, 12)]:
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
# Independently decode only GP immediate and JAL fields using GNU binutils
# nds32 definitions (revision recorded below). This does not validate every
# SLEIGH instruction or prove the global GP value.
def signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value

def gp_displacement(offset):
    word = int.from_bytes(image[offset:offset + 4], 'big')
    assert word >> 25 == 0x1f and word & (1 << 19)
    return signed(word & ((1 << 19) - 1), 19)

crosschecks = {'gp_immediates': 0, 'jal_targets': 0}
for block in blocks:
    for instruction in block['instructions']:
        offset = instruction['address'] - base
        if instruction['mnemonic'] == 'addi.gp':
            displacement = gp_displacement(offset)
            ops = context.translate(image[offset:offset + 16],
                base_address=base + offset, max_instructions=1).ops
            expected = ' = gp + ' + hex(displacement & 0xffffffff)
            assert any(str(op).endswith(expected) for op in ops)
            crosschecks['gp_immediates'] += 1
        elif instruction['mnemonic'] == 'jal':
            word = int.from_bytes(image[offset:offset + 4], 'big')
            assert word >> 25 == 0x24 and word & (1 << 24)
            target = (base + offset + signed(word & 0xffffff, 24) * 2) & 0xffffffff
            assert target == int(instruction['operands'], 16)
            crosschecks['jal_targets'] += 1

def command_table(offset, count):
    address = gp_candidate + gp_displacement(offset)
    position = address - base
    assert 0 <= position < len(image) - count * 8
    return {'address_candidate': address, 'entries': [
        {'command': command, 'handler': handler}
        for command, handler in (struct.unpack_from('<II', image, position + n * 8)
                                 for n in range(count))]}

cid_table = command_table(0x5eb4, 4)
ext_table = command_table(0x776c, 23)
assert {x['command']: x['handler'] for x in cid_table['entries']}[0xed] == 0x10775c
handlers = {x['command']: x['handler'] for x in ext_table['entries']}
assert handlers[8] == 0x1071f8 and handlers[0x11] == 0x106f90 and handlers[0x21] == 0x106708
# Independent LBI/SBI field checks: rt at20, ra at15, byte offset low15.
# These two instructions copy the same register, across calls whose ABI and
# effects are still an explicit external dependency. No 4-bit mask here.
echo_instructions = []
for offset, opcode, register, address_register, displacement in [
        (0x6164, 0, 10, 8, 7), (0x61b0, 8, 10, 6, 5)]:
    raw_instruction = image[offset:offset + 4]
    word = int.from_bytes(raw_instruction, 'big')
    assert word >> 25 == opcode
    assert (word >> 20) & 31 == register
    assert (word >> 15) & 31 == address_register
    assert signed(word & 0x7fff, 15) == displacement
    echo_instructions.append({'address': base + offset,
                              'instruction_hex': raw_instruction.hex()})
raw_result_call_candidates = []
for offset in range(0, len(image) - 40, 2):
    word = int.from_bytes(image[offset:offset + 4], 'big')
    if word >> 25 == 0x24 and word & (1 << 24):
        target = base + offset + signed(word & 0xffffff, 24) * 2
        if target == base + 0x6154:
            raw_result_call_candidates.append(base + offset)
print(json.dumps({
    'image_sha256': identity, 'header_sha256': hashlib.sha256(raw).hexdigest(),
    'load_base': base, 'payload_end': payload_end, 'blocks': blocks,
    'gp_related_pcode': lifted,
    'gp_candidate': gp_candidate,
    'result_sequence_byte_copy': echo_instructions,
    'raw_result_call_candidates': raw_result_call_candidates,
    'sequence_scope': 'Full byte load/store in common result helper only; not end-to-end high-ID acceptance. Raw call candidates may include non-code and omit indirect/tail calls. No domain expansion or reuse enabled.',
    'independent_field_checks': crosschecks,
    'field_definition_source': 'https://gnu.googlesource.com/binutils-gdb/+/3fb6f5457e5b53fdb73a98a24b3764e821e8ccc5/opcodes/nds32-asm.c',
    'cid_table': cid_table, 'extended_table': ext_table,
    'corroboration': {'startup_log_address': log_address, 'startup_log': log,
                      'dispatch_candidate': base + 0xd0,
                      'zero_loop_begin_candidate': payload_end,
                      'zero_loop_end_candidate': gp_candidate - 0x3734},
    'limits': 'GP inferred by equating zero-loop start with payload end; '
              'log and function-start matches corroborate, not prove it. '
              'No instruction execution, complete CFG, relocation or ROM '
              'resolution; only GP immediates/JAL targets independently checked; other decoding needs confirmation.',
    'firmware_ack_contract_verified': False, 'runtime_verified': False,
}, indent=2))
