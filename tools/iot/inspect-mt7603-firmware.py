#!/usr/bin/env python3
"""Identify embedded MT7603 firmware without loading it or asserting ACK semantics."""
import argparse
import hashlib
import json
import re
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('driver', type=Path)
p.add_argument('--command-strings', action='store_true',
               help='Inventory command-related ASCII strings at file offsets; not code or protocol proof')
a = p.parse_args()
images = []
for filename, symbol in (('mt7603_firmware.h', 'MT7603_FirmwareImage'),
                         ('mt7603_e2_firmware.h', 'MT7603_e2_FirmwareImage')):
    path = a.driver / 'include/mcu' / filename
    raw = path.read_bytes()
    text = re.sub(r'/\*.*?\*/|//[^\n]*', '', raw.decode(), flags=re.S)
    arrays = re.findall(r'\bUCHAR\s+' + symbol + r'\s*\[\s*\]\s*=\s*\{([^}]*)\}\s*;', text)
    if len(arrays) != 1:
        p.error('Expected exactly one firmware initializer: ' + filename)
    tokens = arrays[0].strip().rstrip(',').split(',')
    if not all(re.fullmatch(r'\s*0[xX][0-9a-fA-F]{2}\s*', token) for token in tokens):
        p.error('Unsupported firmware initializer token: ' + filename)
    image = bytes(int(token, 16) for token in tokens)
    if len(image) < 36:
        p.error('Truncated firmware trailer: ' + filename)
    declared = int.from_bytes(image[-4:], 'little')
    # AndesMTLoadFwMethod1 adds four CRC bytes to the declared transfer length.
    if declared + 4 + 36 != len(image):
        p.error('Method1 length/trailer mismatch: ' + filename)
    images.append({
        'header': 'include/mcu/' + filename, 'symbol': symbol,
        'header_sha256': hashlib.sha256(raw).hexdigest(),
        'image_sha256': hashlib.sha256(image).hexdigest(),
        'image_bytes': len(image), 'declared_payload_bytes': declared,
        'method1_transfer_bytes': declared + 4, 'trailer_bytes': 36,
        'version_field_hex': image[-29:-19].hex(),
        'version': image[-29:-19].decode('ascii').rstrip('\0'),
        'build_date': image[-19:-4].decode('ascii').rstrip('\0'),
        'crc_verified': False,
    })
    if a.command_strings:
        images[-1]['command_strings'] = [
            {'file_offset': match.start(), 'text': match.group().decode('ascii')}
            for match in re.finditer(rb'[ -~]{6,}', image[:-36])
            if re.search(rb'cmd|event|queue|mail|dispatch|response|channel|power',
                         match.group(), re.I)
        ]
        images[-1]['string_scope'] = (
            'Printable runs in embedded bytes before trailer; offsets are file offsets, '
            'not execution addresses. Strings do not establish instruction decoding, '
            'reachability, firmware ordering or ACK uniqueness.')
print(json.dumps({
    'images': images,
    'scope': 'Embedded initializer identity and Method1 trailer lengths only; '
             'external BIN_FILE_METHOD input and actual hardware selection not verified.',
    'firmware_ack_identity_contract_verified': False,
    'runtime_verified': False,
}, indent=2))
