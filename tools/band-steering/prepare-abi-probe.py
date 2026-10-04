#!/usr/bin/env python3
"""Generate target-only compile probes from actual pinned message declarations."""
import argparse
from pathlib import Path
import hashlib
import json
import re

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
manifest = {'target_compilation_verified': False, 'radios': {}}
for radio in ('mt76x2', 'mt76x3'):
    root = a.source / 'trunk/linux-4.4.x/drivers/net/wireless/mediatek' / radio / 'include'
    header = (root / 'band_steering_def.h').read_text(encoding='utf-8')
    types = (root / 'rtmp_type.h').read_text(encoding='utf-8')
    oid = (root / 'oid.h').read_text(encoding='utf-8')
    mac_lengths = re.findall(r'^\s*#\s*define\s+MAC_ADDR_LEN\s+(\d+)\s*(?:/\*.*?\*/)?\s*$', oid, re.M)
    if mac_lengths != ['6']:
        raise SystemExit('Unexpected pinned MAC address length: ' + radio)
    clean_types = re.sub(r'/\*.*?\*/|//[^\n]*', '', types, flags=re.S)
    aliases = []
    for name in ('UINT8', 'UINT16', 'UINT32', 'UINT64', 'UCHAR', 'ULONG', 'CHAR', 'BOOLEAN'):
        matches = re.findall(r'typedef\s+[^;\n]+\s+' + name + r'\s*;', clean_types)
        if len(matches) != 1:
            raise SystemExit('Unexpected pinned scalar typedef: ' + radio + '/' + name)
        aliases.append(matches[0])
    message = re.search(r'typedef struct _BNDSTRG_MSG\s*\{.*?\}\s*BNDSTRG_MSG\s*,\s*\*PBNDSTRG_MSG\s*;', header, re.S)
    if not message:
        raise SystemExit('Missing actual message definition: ' + radio)
    fields = ['Action']
    if radio == 'mt76x2':
        definitions = message.group(0)
        fields += ['ReturnCode', 'TalbeIndex', 'OnOff', 'Band', 'b2GInfReady', 'b5GInfReady',
                   'Rssi', 'RssiDiff', 'RssiLow', 'FrameType', 'Time', 'ConditionCheck', 'Addr']
    else:
        nvram = re.search(r'typedef struct _bndstrg_nvram_client\s*\{.*?\}\s*BNDSTRG_NVRAM_CLIENT\s*,\s*\*PBNDSTRG_NVRAM_CLIENT\s*;', header, re.S)
        if not nvram:
            raise SystemExit('Missing actual nested NVRAM declaration')
        begin = header.index('struct bnd_msg_heartbeat {')
        definitions = nvram.group(0) + '\n' + header[begin:message.end()]
        fields += ['data', 'data.cli_event', 'data.inf_status_rsp', 'data.onoff', 'data.heartbeat',
                   'data.onoff.Band', 'data.onoff.Channel', 'data.onoff.OnOff',
                   'data.onoff.BndStrgMode', 'data.onoff.ucIfName',
                   'data.cli_add.Addr', 'data.cli_add.TableIndex',
                   'data.cli_del.Addr', 'data.cli_del.TableIndex',
                   'data.inf_status_req.ucIfName', 'data.inf_status_rsp.bInfReady',
                   'data.inf_status_rsp.Channel', 'data.inf_status_rsp.ucIfName',
                   'data.heartbeat.ucIfName', 'data.cli_event.FrameType',
                   'data.cli_event.Band', 'data.cli_event.Channel', 'data.cli_event.Addr',
                   'data.cli_event.data.cli_probe.Rssi', 'data.cli_event.data.cli_auth.Rssi',
                   'data.inf_status_rsp.band', 'data.reject_body.DaemonPid',
                   'data.idle.TableIndex', 'data.idle.ReturnCode', 'data.idle.Addr', 'data.idle.Cookie']
    values = ['0x424e4441u', 'sizeof(void *)', 'sizeof(ULONG)', 'sizeof(UINT64)',
              'sizeof(BNDSTRG_MSG)', '__alignof__(BNDSTRG_MSG)'] + [
              'offsetof(BNDSTRG_MSG, ' + f + ')' for f in fields]
    text = '#include <stddef.h>\n#define MAC_ADDR_LEN 6\n' + '\n'.join(aliases) + '\n' + definitions + '\n'
    text += '_Static_assert(sizeof(void *) == 4 && sizeof(ULONG) == 4, "MIPS32 ABI required");\n'
    text += 'const unsigned int bnd_abi[] __attribute__((used, section(".bndabi"))) = {\n'
    text += ',\n'.join(values) + '\n};\n'
    out = a.output / (radio + '-abi.c')
    with out.open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(text)
    manifest['radios'][radio] = {
        'header_sha256': hashlib.sha256(header.encode()).hexdigest(),
        'scalar_header_sha256': hashlib.sha256(types.encode()).hexdigest(),
        'oid_header_sha256': hashlib.sha256(oid.encode()).hexdigest(),
        'mac_addr_len': int(mac_lengths[0]),
        'fields': ['magic', 'pointer_size', 'ulong_size', 'uint64_size', 'message_size', 'message_alignment'] + fields,
        'probe': out.name,
    }
(a.output / 'abi-probe-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print('Generated two target-only C probes; compile with pinned MIPS GCC and inspect .bndabi, never execute')
