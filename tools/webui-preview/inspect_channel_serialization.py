#!/usr/bin/env python3
"""Record proven Linux ioctl serialization edges; do not infer all driver writers are covered."""
import argparse
import hashlib
import json
import tarfile
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive',type=Path)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
paths=['trunk/linux-4.4.x/net/core/dev_ioctl.c','trunk/linux-4.4.x/net/wireless/wext-core.c']
with tarfile.open(args.archive) as archive:
    files={path:archive.extractfile(path).read() for path in paths}
wext=files[paths[1]].decode()
edge='rtnl_lock();\n\tret = wireless_process_ioctl(net, ifr, cmd, info, standard, private);\n\trtnl_unlock();'
if wext.count(edge)!=1:raise ValueError('WEXT serialization anchor changed')
fallback='return dev->netdev_ops->ndo_do_ioctl(dev, ifr, cmd);'
if wext.count(fallback)!=1:raise ValueError('WEXT legacy driver dispatch changed')
core=files[paths[0]].decode()
private='rtnl_lock();\n\t\t\tret = dev_ifsioc(net, &ifr, cmd);\n\t\t\trtnl_unlock();'
if private not in core or 'cmd >= SIOCDEVPRIVATE' not in core:
    raise ValueError('Private ioctl locking anchor changed')
report={'source_revision':'c25283e915a2a00a763774dd255b14aff997285e',
        'files':{path:hashlib.sha256(raw).hexdigest() for path,raw in files.items()},
        'verified_edges':['WEXT ioctl entry acquires RTNL around wireless_process_ioctl',
                          'WEXT legacy fallback calls ndo_do_ioctl inside that entry',
                          'network private ioctl path invokes dev_ifsioc under RTNL'],
        'not_proven':['all channel-list builders invoked under RTNL','all indirect channel/flag writers serialized',
                      'adapter lifetime through query and policy validation','snapshot remains valid until configuration write/restart'],
        'decision':'RTNL is a candidate existing serialization domain; do not add a reader-only lock or claim complete snapshot safety yet',
        'runtime_verified':False,'new_ioctl_implemented':False}
args.output.write_text(json.dumps(report,indent=2)+'\n')
print('PASS pinned Linux WEXT/private ioctl RTNL edges; driver-wide writer/lifetime proof still open')
