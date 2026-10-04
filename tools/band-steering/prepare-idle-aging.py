#!/usr/bin/env python3
"""Prepare a non-deauth idle-entry query in the exact pinned mt76x3 source."""
import argparse
import hashlib
import json
from pathlib import Path

HEADER_SHA = 'c775bd46ed88c6b93e03b0025b3ba0c97e0df17fb086846e8d808262584c840c'
SOURCE_SHA = '598bc96fb307175609f8fb4df8626858c33a53751165a32c9b1f6ca6cae7ceae'
CASE = '''\t\tcase WR_IDLE_QUERY: {
            struct bnd_msg_idle request = msg->data.idle;
            BNDSTRG_MSG response = { 0 };
            struct bnd_msg_idle *reply = &response.data.idle;
            MAC_TABLE_ENTRY *station;
            PBND_STRG_CLI_ENTRY idle_entry;

            if (Status != 0 || wrq->u.data.length != sizeof(BNDSTRG_MSG) ||
                request.TableIndex >= BND_STRG_MAX_TABLE_SIZE || request.Cookie == 0)
                return BND_STRG_INVALID_ARG;
            response.Action = WR_IDLE_RSP;
            *reply = request;
            reply->ReturnCode = 2; /* error: retain userspace record */
            station = MacTableLookup(pAd, request.Addr);
            if (station) {
                reply->ReturnCode = 1; /* present, including authentication in progress */
            } else {
                idle_entry = BndStrg_TableLookup(table, request.Addr);
                if (!idle_entry) {
                    reply->ReturnCode = 0;
                } else if (idle_entry->TableIndex == request.TableIndex) {
                    /* Delete only the steering record; never a MAC-table entry.
                     * An association racing this check is not deauthenticated. */
                    if (BndStrg_DeleteEntry(table, request.Addr, 0xff) == BND_STRG_SUCCESS)
                        reply->ReturnCode = 0;
                }
            }
            BndStrgSendMsg(pAd, &response);
            break;
        }
'''

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Pinned source anchor changed: ' + repr(old))
    return text.replace(old, new)

def prepare(root):
    radio = root / 'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3'
    files = [(radio / 'include/band_steering_def.h', HEADER_SHA),
             (radio / 'ap/ap_band_steering.c', SOURCE_SHA)]
    for path, expected in files:
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('Unexpected pinned input: ' + str(path))
    header = files[0][0].read_text(encoding='utf-8')
    source = files[1][0].read_text(encoding='utf-8')
    header = replace_once(header, '\tUPDATE_WHITE_BLACK_LIST,\n',
        '\tUPDATE_WHITE_BLACK_LIST,\n\tWR_IDLE_QUERY = 0x70,\n\tWR_IDLE_RSP = 0x71,\n')
    header = replace_once(header, 'struct bnd_msg_cli_probe {', '''/* WR1200JS non-deauth idle-entry protocol extension. */
struct bnd_msg_idle {
    UINT8 TableIndex;
    UINT8 ReturnCode;
    UCHAR Addr[MAC_ADDR_LEN];
    UINT32 Cookie;
};

struct bnd_msg_cli_probe {''')
    header = replace_once(header, '        struct bnd_msg_reject_body reject_body;',
        '        struct bnd_msg_reject_body reject_body;\n        struct bnd_msg_idle idle;')
    source = replace_once(source, '\t\tcase CLI_ADD: {', CASE + '\t\tcase CLI_ADD: {')
    report = {'upstream_revision': 'c25283e915a2a00a763774dd255b14aff997285e',
              'runtime_verified': False, 'files': []}
    for (path, original), text in zip(files, (header, source)):
        with path.open('w', encoding='utf-8', newline='\n') as stream:
            stream.write(text)
        report['files'].append({'path': str(path.relative_to(root)).replace('\\', '/'),
                               'original_sha256': original,
                               'prepared_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (root / 'band-steering-idle-preparation.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
