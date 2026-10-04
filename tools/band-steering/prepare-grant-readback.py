#!/usr/bin/env python3
"""Add read-only, correlated steering-record queries to the pinned drivers."""
import argparse
import hashlib
import json
from pathlib import Path

LEGACY_SHA = '0a914a042f31419cc92da3ed51e5b642b4b6ec4ff9b3c656ec8c0973bad11a0c'
MODERN_SHA = '0749e092f6cf95bf775b8a950fb2f2d07bd61e406fa9b298da7e67e4b95e1edf'
LEGACY_CASE = '''\t\tcase 0x72: { /* WR_GRANT_QUERY: inspect only; never insert or delete. */
            BNDSTRG_MSG response = { 0 };
            if (msg->TalbeIndex >= BND_STRG_MAX_TABLE_SIZE || msg->Time == 0)
                break;
            response.Action = 0x73;
            response.TalbeIndex = msg->TalbeIndex;
            response.Time = msg->Time;
            COPY_MAC_ADDR(response.Addr, msg->Addr);
            response.ReturnCode = 2;
            if (table->Ops && table->Ops->TableLookup)
                response.ReturnCode = table->Ops->TableLookup(table, msg->Addr) ? 1 : 0;
            D_BndStrgSendMsg(pAd, &response);
            break;
        }
'''
MODERN_CASE = '''\t\tcase 0x72: { /* WR_GRANT_QUERY: inspect only; never insert or delete. */
            struct bnd_msg_idle request = msg->data.idle;
            BNDSTRG_MSG response = { 0 };
            PBND_STRG_CLI_ENTRY found;
            if (Status != 0 || wrq->u.data.length != sizeof(BNDSTRG_MSG) ||
                request.TableIndex >= BND_STRG_MAX_TABLE_SIZE || request.Cookie == 0)
                return BND_STRG_INVALID_ARG;
            response.Action = 0x73;
            response.data.idle = request;
            found = BndStrg_TableLookup(table, request.Addr);
            response.data.idle.ReturnCode = !found ? 0 :
                (found->TableIndex == request.TableIndex ? 1 : 2);
            BndStrgSendMsg(pAd, &response);
            break;
        }
'''

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Source anchor drift: ' + repr(old))
    return text.replace(old, new)

def prepare(root):
    parent = root / 'trunk/linux-4.4.x/drivers/net/wireless/mediatek'
    inputs = [(parent / 'mt76x2/ap/ap_band_steering.c', LEGACY_SHA),
              (parent / 'mt76x3/ap/ap_band_steering.c', MODERN_SHA)]
    texts = []
    for path, expected in inputs:
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError('Pinned source mismatch: ' + str(path))
        texts.append(raw.decode('utf-8'))
    legacy = replace_once(texts[0], '\t\tcase CLI_ADD:', LEGACY_CASE + '\t\tcase CLI_ADD:')
    # The original legacy dispatcher ignored copy failures and could process
    # uninitialized message bytes. Reject failed copies before any dispatch.
    legacy = replace_once(legacy,
        '\t\tcopy_from_user(&msg, wrq->u.data.pointer, wrq->u.data.length);',
        '\t\tif (copy_from_user(&msg, wrq->u.data.pointer, wrq->u.data.length))\n'
        '\t\t\treturn BND_STRG_INVALID_ARG;')
    modern = replace_once(texts[1], '\t\tcase CLI_ADD: {', MODERN_CASE + '\t\tcase CLI_ADD: {')
    report = {'upstream_revision': 'c25283e915a2a00a763774dd255b14aff997285e',
              'runtime_verified': False, 'files': []}
    for (path, original), text in zip(inputs, (legacy, modern)):
        with path.open('w', encoding='utf-8', newline='\n') as out:
            out.write(text)
        report['files'].append({'path': str(path.relative_to(root)).replace('\\', '/'),
            'original_sha256': original, 'prepared_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (root / 'band-steering-grant-preparation.json').write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    print(json.dumps(prepare(parser.parse_args().source), indent=2))
