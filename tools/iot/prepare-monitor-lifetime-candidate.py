#!/usr/bin/env python3
"""Stage a source-pinned monitor registration failure cleanup candidate.

The input driver is read-only. This does not install into firmware sources.
"""
import argparse
import hashlib
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
source = args.source.resolve()
output = args.output.resolve()
if output.exists() or output == source or source in output.parents:
    raise SystemExit('Output must be new and separate from source')

name = Path('sniffer/sniffer_radiotap.c')
raw = (source / name).read_bytes()
blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
if blob != 'be4871c082ab8d50c41bf3d1edf8f9f7d29ec340':
    raise SystemExit('Unreviewed monitor source bytes')
text = raw.decode('utf-8')

old = '''\t\tRtmpOSNetDevFree(new_dev_p);
\t\treturn;
\t}

\t/* init MAC address of virtual network interface */'''
new = '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,31)
\t\tvfree((void *)new_dev_p->netdev_ops);
#endif
\t\tRtmpOSNetDevFree(new_dev_p);
\t\twdev->if_dev = NULL;
\t\treturn;
\t}

\t/* init MAC address of virtual network interface */'''
if text.count(old) != 1:
    raise SystemExit('Changed index-registration failure path')
text = text.replace(old, new, 1)

old = '''\tRtmpOSNetDevAttach(pAd->OpMode, new_dev_p, pNetDevOps);
\tpAd->monitor_ctrl.monitor_initiated = TRUE;'''
new = '''\tif (wr_iot_netdev_attach_checked(pAd, pAd->OpMode, new_dev_p, pNetDevOps) != NDIS_STATUS_SUCCESS) {
\t\trtmp_wdev_idx_unreg(pAd, wdev);
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,31)
\t\tvfree((void *)new_dev_p->netdev_ops);
#endif
\t\tRtmpOSNetDevFree(new_dev_p);
\t\twdev->if_dev = NULL;
\t\treturn;
\t}
\tpAd->monitor_ctrl.monitor_initiated = TRUE;'''
if text.count(old) != 1:
    raise SystemExit('Changed monitor attach path')
text = text.replace(old, new, 1)

old = '\t\tRtmpOSNetDevProtect(1);\n\t\tRtmpOSNetDevDetach(wdev->if_dev);'
new = ('\t\tif (wr_iot_netdev_mark_removing(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS)\n'
       '\t\t\treturn;\n\t\tRtmpOSNetDevProtect(1);\n\t\tRtmpOSNetDevDetach(wdev->if_dev);')
if text.count(old) != 1:
    raise SystemExit('Changed monitor remove anchor')
text = text.replace(old, new, 1)

target = output / name
target.parent.mkdir(parents=True)
patched = text.encode('utf-8')
target.write_bytes(patched)
(output / 'manifest.json').write_text(json.dumps({
    'production_installed': False,
    'source_path': name.as_posix(),
    'original_git_blob': blob,
    'candidate_sha256': hashlib.sha256(patched).hexdigest(),
}, indent=2) + '\n', encoding='utf-8')
print(target)
