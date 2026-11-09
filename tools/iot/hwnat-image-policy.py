#!/usr/bin/env python3
"""Inspect WR1200JS embedded HNAT policy; no runtime isolation claim."""
import hashlib
import lzma
import struct

MAX_DTB_BYTES = 2 * 1024 * 1024
MAX_DTB_PARSE_BYTES = 8 * 1024 * 1024


def fdt_properties(blob):
    if len(blob) > MAX_DTB_BYTES:
        raise ValueError('FDT exceeds inspection limit')
    if len(blob) < 40:
        raise ValueError('short FDT header')
    magic, total, off_struct, off_strings, off_reserve, version, compatible, cpu, strings_size, struct_size = struct.unpack_from('>10I', blob)
    if magic != 0xd00dfeed or total != len(blob) or version < 17 or compatible > 17:
        raise ValueError('unsupported FDT header')
    if off_reserve % 8 or off_struct % 4:
        raise ValueError('misaligned FDT blocks')
    if not (40 <= off_reserve <= total - 16 and 40 <= off_struct <= total and
            40 <= off_strings <= total and off_struct + struct_size <= total and
            off_strings + strings_size <= total):
        raise ValueError('FDT block outside blob')
    if off_struct < off_strings + strings_size and off_strings < off_struct + struct_size:
        raise ValueError('overlapping FDT blocks')
    strings = blob[off_strings:off_strings + strings_size]
    cursor, limit = off_struct, off_struct + struct_size
    stack, properties, nodes = [], {}, set()
    while cursor + 4 <= limit:
        token = struct.unpack_from('>I', blob, cursor)[0]
        cursor += 4
        if token == 1:
            end = blob.find(b'\0', cursor, limit)
            if end < 0:
                raise ValueError('unterminated FDT node')
            name = blob[cursor:end].decode('ascii')
            if '/' in name or (not stack and (name or nodes)):
                raise ValueError('invalid FDT root/node')
            if len(stack) >= 64 or len(nodes) >= 8192 or len(name) > 255:
                raise ValueError('FDT node/depth limit')
            stack.append(name)
            path = '/'.join(stack)
            if len(path) > 4096:
                raise ValueError('FDT path limit')
            if path in nodes:
                raise ValueError('duplicate FDT node')
            nodes.add(path)
            cursor = (end + 4) & ~3
        elif token == 2:
            if not stack:
                raise ValueError('unbalanced FDT node')
            stack.pop()
        elif token == 3:
            if not stack or cursor + 8 > limit:
                raise ValueError('FDT property outside node')
            length, offset = struct.unpack_from('>II', blob, cursor)
            cursor += 8
            end = strings.find(b'\0', offset) if offset < len(strings) else -1
            if end < 0 or cursor + length > limit:
                raise ValueError('FDT property outside block')
            name = strings[offset:end].decode('ascii')
            if len(name) > 255 or len(properties) >= 16384:
                raise ValueError('FDT property limit')
            key = ('/'.join(stack), name)
            if key in properties:
                raise ValueError('duplicate FDT property')
            properties[key] = blob[cursor:cursor + length]
            cursor = (cursor + length + 3) & ~3
        elif token == 4:
            pass
        elif token == 9:
            if stack or not nodes or cursor != limit:
                raise ValueError('invalid FDT end')
            return properties
        else:
            raise ValueError('invalid FDT token')
    raise ValueError('missing FDT end')


def string_list(properties, node, key):
    value = properties.get((node, key), b'')
    if not value or not value.endswith(b'\0'):
        raise ValueError('missing or invalid DTB property: ' + key)
    result = value[:-1].decode('ascii').split('\0')
    if any(not item for item in result):
        raise ValueError('empty DTB string: ' + key)
    return result


def inspect_image(data):
    if len(data) < 64 or data[:4] != bytes.fromhex('27051956') or data[31] != 3:
        raise ValueError('expected LZMA uImage')
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE, memlimit=128 * 1024 * 1024)
    kernel = decoder.decompress(data[64:], max_length=64 * 1024 * 1024 + 1)
    if not decoder.eof or len(kernel) > 64 * 1024 * 1024:
        raise ValueError('kernel stream truncated or exceeds inspection limit')
    candidates, offset, attempts, parsed_bytes = [], 0, 0, 0
    while True:
        offset = kernel.find(bytes.fromhex('d00dfeed'), offset)
        if offset < 0:
            break
        start, offset = offset, offset + 4
        if start % 4 or start + 40 > len(kernel):
            continue
        size = struct.unpack_from('>I', kernel, start + 4)[0]
        if size < 40 or size > MAX_DTB_BYTES or start + size > len(kernel):
            continue
        attempts += 1
        parsed_bytes += size
        if attempts > 128 or parsed_bytes > MAX_DTB_PARSE_BYTES:
            raise ValueError('FDT candidate inspection limit')
        blob = kernel[start:start + size]
        try:
            properties = fdt_properties(blob)
            candidates.append((blob, properties))
        except (ValueError, UnicodeError):
            continue
        if len(candidates) > 1:
            raise ValueError('ambiguous embedded DTBs')
    if len(candidates) != 1:
        raise ValueError('expected one unambiguous WR1200JS embedded DTB')
    blob, properties = candidates[0]
    if string_list(properties, '', 'model') != ['YouHua WR1200JS']:
        raise ValueError('foreign embedded DTB model')
    node = '/hnat@1e100000'
    devices = string_list(properties, node, 'ext-devices')
    if len(devices) != len(set(devices)) or any(len(item) > 15 for item in devices):
        raise ValueError('invalid or duplicate external devices')
    forbidden = sorted(set(devices) & {'ra2', 'rai2', 'br-iot'})
    if forbidden:
        raise ValueError('IoT device in HNAT external list: ' + ', '.join(forbidden))
    if not {'ra0', 'rai0'}.issubset(devices):
        raise ValueError('audited Main Wi-Fi external device missing')
    lan = string_list(properties, node, 'mtketh-lan')
    wan = string_list(properties, node, 'mtketh-wan')
    if lan != ['eth2'] or wan != ['eth3']:
        raise ValueError('WR1200JS LAN/WAN HNAT mapping changed')
    return {'scope': 'Embedded DTB HNAT policy only; no packet/runtime proof',
            'external_devices': devices, 'lan': lan, 'wan': wan,
            'dtb_sha256': hashlib.sha256(blob).hexdigest(),
            'kernel_sha256': hashlib.sha256(kernel).hexdigest(),
            'runtime_verified': False}
