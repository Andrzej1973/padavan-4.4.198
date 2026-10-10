#!/usr/bin/env python3
"""Extract actual station types for target layout checks, without rate decoding."""
import argparse
import re
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--output', required=True, type=Path)
a = p.parse_args()
code = '#include <stddef.h>\n#include <stdint.h>\ntypedef unsigned char UCHAR;\ntypedef signed char CHAR;\ntypedef uint32_t UINT32;\ntypedef unsigned short USHORT;\n#define MAC_ADDR_LEN 6\n#define ETHER_ADDR_LEN 6\n#define MAX_NUMBER_OF_MAC 64\n'
for name, path in [('shared', 'trunk/user/shared/include/ralink_priv.h')] + [(r, 'trunk/linux-4.4.x/drivers/net/wireless/mediatek/' + r + '/include/oid.h') for r in ('mt76x2', 'mt76x3')]:
    s = (a.source / path).read_text(encoding='utf-8')
    for kind, type_name, pointer in [('union', 'MACHTTRANSMIT_SETTING', 'PMACHTTRANSMIT_SETTING'), ('struct', 'RT_802_11_MAC_ENTRY', 'PRT_802_11_MAC_ENTRY'), ('struct', 'RT_802_11_MAC_TABLE', 'PRT_802_11_MAC_TABLE')]:
        match = re.search(r'typedef ' + kind + r' _' + type_name + r'\s*\{.*?' + pointer + ';', s, re.S)
        assert match, (name, type_name)
        text = match.group()
        for token in ('MACHTTRANSMIT_SETTING', 'PMACHTTRANSMIT_SETTING', '_MACHTTRANSMIT_SETTING', 'RT_802_11_MAC_ENTRY', 'PRT_802_11_MAC_ENTRY', '_RT_802_11_MAC_ENTRY', 'RT_802_11_MAC_TABLE', 'PRT_802_11_MAC_TABLE', '_RT_802_11_MAC_TABLE'):
            text = re.sub(r'\b' + token + r'\b', name + '_' + token, text)
        code += text + '\n'
    table = name + '_RT_802_11_MAC_TABLE'
    code += '_Static_assert(offsetof(' + table + ',Entry)==sizeof(unsigned long),"table header");\n'
    code += '_Static_assert(sizeof(' + table + ')==sizeof(unsigned long)+64*28,"64 client table");\n'
    t = name + '_RT_802_11_MAC_ENTRY'
    code += '_Static_assert(sizeof(' + t + ')==28,"entry size");\n'
    for field, offset in [('ApIdx',0), ('Addr',1), ('AvgRssi0',10), ('AvgRssi1',11), ('AvgRssi2',12), ('ConnectedTime',16), ('TxRate',20), ('LastRxRate',24)]:
        code += '_Static_assert(offsetof(' + t + ',' + field + ')==' + str(offset) + ',"' + field + '");\n'
code += 'int main(void){return 0;}\n'
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(code, encoding='utf-8')
print('Generated actual station-type layout assertions; compile with the target compiler')
