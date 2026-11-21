#!/usr/bin/env python3
"""Stage source-pinned AP-client/WDS registration cleanup outside firmware."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
root, out = a.source.resolve(), a.output.resolve()
if out.exists() or out == root or root in out.parents:
    raise SystemExit('Output must be new and separate from source')

blobs = {
    'ap/ap_apcli.c': '10336b6b5f22209817035628a907cacb7a54b033',
    'ap/ap_wds.c': 'e4dedddf254632b528b67f295b06635ec8b5f7b6',
}

def once(s, old, new, path):
    if s.count(old) != 1:
        raise SystemExit('Changed ' + path + ' insertion anchor')
    return s.replace(old, new, 1)

files = {}
for name, expected in blobs.items():
    data = (root / name).read_bytes()
    actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if actual != expected:
        raise SystemExit('Unreviewed ' + name + ' source bytes')
    files[name] = data.decode('utf-8')

cleanup = ("#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,31)\n"
           "\t\t\tvfree((void *)DEV->netdev_ops);\n"
           "#endif\n"
           "\t\t\tRtmpOSNetDevFree(DEV);\n"
           "\t\t\twdev->if_dev = NULL;")

name = 'ap/ap_apcli.c'
s = files[name]
s = once(s, '\t\t\tRtmpOSNetDevFree(new_dev_p);\n\t\t\tbreak;',
         cleanup.replace('DEV', 'new_dev_p') + '\n\t\t\tbreak;', name)
s = once(s, '\t\tRtmpOSNetDevAttach(pAd->OpMode, new_dev_p, pNetDevOps);',
         '''\t\tif (wr_iot_netdev_attach_checked(pAd, pAd->OpMode, new_dev_p, pNetDevOps) != NDIS_STATUS_SUCCESS) {
\t\t\trtmp_wdev_idx_unreg(pAd, wdev);
''' + cleanup.replace('DEV', 'new_dev_p') + '''
\t\t\tbreak;
\t\t}''', name)
s = once(s, '\tpAd->flg_apcli_init = TRUE;\n\n}',
         '\tpAd->flg_apcli_init = (idx > 0) ? TRUE : FALSE;\n\n}', name)
s = once(s, '\t\t\tRtmpOSNetDevProtect(1);\n\t\t\tRtmpOSNetDevDetach(wdev->if_dev);',
         '\t\t\tif (wr_iot_netdev_mark_removing(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS)\n\t\t\t\tcontinue;\n\t\t\tRtmpOSNetDevProtect(1);\n\t\t\tRtmpOSNetDevDetach(wdev->if_dev);', name)
files[name] = s

name = 'ap/ap_wds.c'
s = files[name]
s = once(s, '\t\t\tRtmpOSNetDevFree(pWdsNetDev);\n\t\t\tbreak;',
         cleanup.replace('DEV', 'pWdsNetDev') + '\n\t\t\tbreak;', name)
s = once(s, '\t\tRtmpOSNetDevAttach(pAd->OpMode, pWdsNetDev, pNetDevOps);',
         '''\t\tif (wr_iot_netdev_attach_checked(pAd, pAd->OpMode, pWdsNetDev, pNetDevOps) != NDIS_STATUS_SUCCESS) {
\t\t\trtmp_wdev_idx_unreg(pAd, wdev);
''' + cleanup.replace('DEV', 'pWdsNetDev') + '''
\t\t\tbreak;
\t\t}''', name)
s = once(s, '\t\t\tRtmpOSNetDevProtect(1);\n\t\t\tRtmpOSNetDevDetach(wdev->if_dev);',
         '\t\t\tif (wr_iot_netdev_mark_removing(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS)\n\t\t\t\tcontinue;\n\t\t\tRtmpOSNetDevProtect(1);\n\t\t\tRtmpOSNetDevDetach(wdev->if_dev);', name)
files[name] = s

records = []
for name, text in files.items():
    target = out / name
    target.parent.mkdir(parents=True, exist_ok=True)
    data = text.encode('utf-8')
    target.write_bytes(data)
    records.append({'path': name, 'original_git_blob': blobs[name],
                    'candidate_sha256': hashlib.sha256(data).hexdigest()})
(out / 'manifest.json').write_text(json.dumps({
    'production_installed': False, 'files': records,
}, indent=2) + '\n', encoding='utf-8')
print('Staged AP-client/WDS netdev failure cleanup; production unchanged')
