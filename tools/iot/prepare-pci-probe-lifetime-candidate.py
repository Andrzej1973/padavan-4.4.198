#!/usr/bin/env python3
"""Stage exact-source PCI probe attach failure cleanup; no driver install."""
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
name = Path('os/linux/pci_main_dev.c')
raw = (root / name).read_bytes()
blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
if blob != 'eb1118e720e49741261314226a5cc9f9f6ede150':
    raise SystemExit('Unreviewed PCI source bytes')
text = raw.decode('utf-8')
old = '''err_out_free_netdev:
\tRtmpOSNetDevFree(net_dev);
\t
err_out_free_radev:'''
new = '''err_out_free_netdev:
\t/* Attach failed after pci_set_drvdata and netdev_ops allocation. */
\tpci_set_drvdata(pdev, NULL);
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,31)
\tvfree((void *)net_dev->netdev_ops);
#endif
\tRtmpOSNetDevFree(net_dev);
\t
err_out_free_radev:'''
if text.count(old) != 1:
    raise SystemExit('Changed PCI attach-failure cleanup anchor')
text = text.replace(old, new, 1)
attach_old = 'rv = RtmpOSNetDevAttach(OpMode, net_dev, &netDevHook);'
attach_new = 'rv = wr_iot_netdev_attach_checked(pAd, OpMode, net_dev, &netDevHook);'
if text.count(attach_old) != 1:
    raise SystemExit('Changed PCI main attach anchor')
patched = text.replace(attach_old, attach_new, 1).encode('utf-8')
target = out / name
target.parent.mkdir(parents=True)
target.write_bytes(patched)
(out / 'manifest.json').write_text(json.dumps({
    'production_installed': False, 'original_git_blob': blob,
    'candidate_sha256': hashlib.sha256(patched).hexdigest(),
}, indent=2) + '\n', encoding='utf-8')
print('Staged PCI attach-failure cleanup; production unchanged')
