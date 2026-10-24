#!/usr/bin/env python3
"""Stage shared enqueue implementation with truthful opt-in status, not installed."""
import argparse
import hashlib
import json
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
root, out = a.source.resolve(), a.output.resolve()
if out.exists() or out == root or root in out.parents or out in root.parents:
    raise SystemExit('Output must be new and separate')
src = root / 'common/cmm_cmd.c'
data = src.read_bytes()
blob = 'c053649a0c8c12edf459300af022b64ff26d2fca'
if hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() != blob:
    raise SystemExit('Unreviewed enqueue source')
text = data.decode('utf-8')
start = text.index('NDIS_STATUS RTEnqueueInternalCmd(')
body = text.index('\n{', start)
end = text.index('\n}', body) + 2
function = text[body:end]
old = '\treturn(NDIS_STATUS_SUCCESS);'
if function.count(old) != 1:
    raise SystemExit('Changed final enqueue return')
function = function.replace(old, '\treturn truthful ? status : NDIS_STATUS_SUCCESS;', 1)
signature = '''static NDIS_STATUS wr_enqueue_internal_cmd(
 PRTMP_ADAPTER pAd, NDIS_OID Oid, PVOID pInformationBuffer,
 UINT32 InformationBufferLength, BOOLEAN truthful)'''
wrappers = '''
NDIS_STATUS RTEnqueueInternalCmd(PRTMP_ADAPTER pAd, NDIS_OID Oid,
 PVOID buffer, UINT32 length)
{
 return wr_enqueue_internal_cmd(pAd, Oid, buffer, length, FALSE);
}
/* Internal candidate only: caller must separately own its queued result. */
NDIS_STATUS wr_iot_enqueue_internal_cmd(PRTMP_ADAPTER pAd, NDIS_OID Oid,
 PVOID buffer, UINT32 length)
{
 return wr_enqueue_internal_cmd(pAd, Oid, buffer, length, TRUE);
}
'''
unit = signature + function + wrappers
if src.read_bytes() != data:
    raise SystemExit('Source changed')
(out / 'common').mkdir(parents=True)
(out / 'common/cmm_cmd.c').write_text(text[:start]+unit+text[end:], encoding='utf-8')
(out / 'checked-enqueue.inc').write_text(unit, encoding='utf-8')
(out / 'manifest.json').write_text(json.dumps({
 'original_git_blob': blob, 'production_installed': False,
 'issuer_bound': False, 'queued_result_lifetime_proven': False,
 'target_compiled': False,
}, indent=2)+'\n', encoding='utf-8')
print('Prepared shared checked enqueue candidate; no issuer or production installation')
