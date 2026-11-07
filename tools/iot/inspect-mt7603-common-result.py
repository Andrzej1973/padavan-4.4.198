#!/usr/bin/env python3
"""Compare exact E1/E2 result helpers statically; no firmware execution or reuse grant."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import pypcode

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('driver', type=Path)
a = p.parse_args()
records = []
for filename, symbol, digest, start, end, load, store in [
    ('mt7603_firmware.h', 'MT7603_FirmwareImage',
     'e1d9cabeeb7d1539ea94665f3e7527968166552e9fc28171e0af7dbaa34ac3a5',
     0x6448, 0x64fc, 0x6458, 0x64bc),
    ('mt7603_e2_firmware.h', 'MT7603_e2_FirmwareImage',
     'e897b5ca7277d77778dda75450956143709e39005affaf2b682c1e7d79fc4c64',
     0x6154, 0x61e8, 0x6164, 0x61b0),
]:
    raw = (a.driver / 'include/mcu' / filename).read_bytes()
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', raw.decode(), flags=re.S)
    arrays = re.findall(r'\bUCHAR\s+' + symbol + r'\s*\[\s*\]\s*=\s*\{([^}]*)\}', text)
    assert len(arrays) == 1
    tokens = arrays[0].strip().rstrip(',').split(',')
    assert all(re.fullmatch(r'\s*0[xX][0-9a-fA-F]{2}\s*', x) for x in tokens)
    image = bytes(int(x, 16) for x in tokens)
    assert hashlib.sha256(image).hexdigest() == digest
    context = pypcode.Context('NDS32:BE:32:default')
    instructions = context.disassemble(image[start:end + 16], base_address=0x100000 + start,
                                       max_instructions=(end-start)//4).instructions
    assert instructions[-1].mnem == 'ret'
    # Independent GNU NDS32 opcode/register/immediate field checks.
    for offset, opcode, base_register, displacement in [(load, 0, 8, 7), (store, 8, 6, 5)]:
        word = int.from_bytes(image[offset:offset+4], 'big')
        assert word >> 25 == opcode
        assert (word >> 20) & 31 == 10  # s4
        assert (word >> 15) & 31 == base_register
        assert word & 0x7fff == displacement
    # Resolve only adjacent constant sethi/ori followed by jral lp,ta.
    calls = []
    for n, instruction in enumerate(instructions):
        if instruction.mnem == 'jral' and instruction.body == 'lp,ta':
            high, low = instructions[n-2:n]
            assert high.mnem == 'sethi' and high.body.startswith('ta, ')
            assert low.mnem == 'ori' and low.body.startswith('ta, ta, ')
            calls.append({'site': instruction.addr.offset,
                          'target': (int(high.body.split(',')[-1], 0) << 12) |
                                    int(low.body.split(',')[-1], 0)})
        elif instruction.mnem == 'jal':
            calls.append({'site': instruction.addr.offset, 'target': int(instruction.body, 16)})
    records.append({'header': filename, 'image_sha256': digest,
                    'helper_address': 0x100000+start, 'sequence_load': 0x100000+load,
                    'sequence_store': 0x100000+store,
                    'calls': calls, 'instructions': [
                        {'address': i.addr.offset, 'mnemonic': i.mnem, 'operands': i.body}
                        for i in instructions]})
assert [x['target'] for x in records[0]['calls']] == [0x317c, 0x310c, 0x24e4, 0x3a74]
assert [x['target'] for x in records[1]['calls']] == [0x2d38, 0x2cdc, 0x21c8, 0x3540]
print(json.dumps({'images': records,
    'conclusion': 'Both exact-image common result helpers copy full request byte7 to output byte5. Their four external call addresses differ.',
    'limits': 'Helper identity/call role inferred from structure. No ROM implementation, calling-convention proof, full path coverage, high-ID support, duplicate bound or safe reuse established.',
    'runtime_verified': False, 'reuse_enabled': False}, indent=2))
