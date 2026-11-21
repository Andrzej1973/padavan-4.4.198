#!/usr/bin/env python3
"""Keep private netdev_ops through RTNL retirement; release once with netdev."""
import argparse,hashlib,shutil,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'os/linux/rt_linux.c':'11519eab5fe7640eed2dd50751cd31b3f22921439d961edda9e3e1097ca8d10e',
 'os/linux/pci_main_dev.c':'956be6cbf2e22e0d21e38c4be7f2806f5d642b333223da317fbf63b6845a062c',
 'ap/ap_mbss.c':'aa1beab99db88dbc58ffd65482eb2169b98abf1869187d552c2992d832cb6d70',
 'ap/ap_apcli.c':'46ea5e20990ad68fe563069dc831546116a55b523463029f933166bde880593f',
 'ap/ap_wds.c':'d49c3061063f3711a28a7e70dfe9ccca3c805b0a23ca941dbf1d4bcfc91cef99',
 'sniffer/sniffer_radiotap.c':'21d1d652f33ff35e80c87f405466d145c35cca210c46e2a989395c67d8c5770a'}
texts={}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=(src/name).read_text()
def one(name,old,new,count=1):
 if texts[name].count(old)!=count:p.error('changed anchor: '+name+': '+old)
 texts[name]=texts[name].replace(old,new)
name='os/linux/rt_linux.c';s=texts[name];sig='void RtmpOSNetDevDetach(PNET_DEV pNetDev)'
start=s.index(sig);end=s.index('\n}',start)+2
texts[name]=s[:start]+sig+'''
{
 /* Caller holds RTNL; keep private ops through netdev_run_todo/ref drain. */
 unregister_netdevice(pNetDev);
}
'''+s[end:]
anchor='void RtmpOSNetDevFree(PNET_DEV pNetDev)\n{\n\tASSERT(pNetDev);'
one(name,anchor,anchor+'''
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,31)
 /* Private per-device allocation from RtmpOSNetDevCreate. Registered callers
  * must have completed RTNL unlock/reference drain before entering Free. */
 vfree((void *)pNetDev->netdev_ops);
 pNetDev->netdev_ops = NULL;
#endif''')
one(name,'''        /* This private ops allocation has not been handed to Detach. */
        vfree(pNetDevOps);
        pNetDev->netdev_ops = NULL;''',
 '        /* RtmpOSNetDevFree owns the private ops allocation on failure too. */')
one('ap/ap_mbss.c','''    vfree(dev->netdev_ops);
    dev->netdev_ops = NULL;''','    /* Private ops are released by RtmpOSNetDevFree. */')
one('ap/ap_mbss.c',' * Normal Detach owns the ops allocation for registered devices.',
 ' * The common Free helper owns private ops for registered and unregistered devices.')
for rel,ptr,count in [('ap/ap_apcli.c','new_dev_p',2),('ap/ap_wds.c','pWdsNetDev',2),
 ('sniffer/sniffer_radiotap.c','new_dev_p',2),('os/linux/pci_main_dev.c','net_dev',1)]:
 one(rel,'vfree((void *)'+ptr+'->netdev_ops);',
  '/* Private ops are released once by RtmpOSNetDevFree. */',count)
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
out.with_name(out.name+'-manifest.json').write_text(json.dumps({'input_sha256':pins,
 'scope':'private netdev_ops allocation lifetime only',
 'target_compiled':False,'runtime_verified':False,'vendor_callbacks_joined':False},indent=2)+'\n')
print('Staged private ops release with netdev Free, not inside Detach or duplicate failure paths')
