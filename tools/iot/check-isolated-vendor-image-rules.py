#!/usr/bin/env python3
"""Dry-run actual pinned vendor rules with isolated ROMFS/image destinations."""
import argparse,subprocess,tarfile,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);a=p.parse_args()
with tempfile.TemporaryDirectory(prefix='wr-vendor-image-rules-') as d:
 root=Path(d);trunk=root/'trunk';trunk.mkdir()
 with tarfile.open(a.archive) as archive:
  for name in ['vendors/Makefile','vendors/vendors-common.mak','vendors/Ralink/Makefile']:
   item=archive.getmember('trunk/'+name)
   if not item.isfile():raise ValueError('Nonregular pinned rule '+name)
   dest=trunk/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(archive.extractfile(item).read())
 (trunk/'.config').write_text('CONFIG_VENDOR=Ralink\nCONFIG_PRODUCT=MT7621\nCONFIG_FIRMWARE_PRODUCT_ID=WR1200JS\n')
 (trunk/'config.arch').write_text('')
 (trunk/'linux-4.4.x').mkdir();(trunk/'linux-4.4.x/.config').write_text('# kernel fixture\n')
 output=root/'isolated';output.mkdir();romfs=output/'romfs';romfs.mkdir();images=output/'images';images.mkdir()
 command=['make','-n','-C',str(trunk/'vendors'),'romfs.post','image',
          'ROOTDIR='+str(trunk),'ROMFSDIR='+str(romfs),'IMAGEDIR='+str(images),
          'LINUXDIR=linux-4.4.x','LINUX_CONFIG='+str(trunk/'linux-4.4.x/.config'),
          'PROJECT_CONFIG='+str(trunk/'.config'),'ARCH_CONFIG='+str(trunk/'config.arch'),
          'FIRMWARE_KERNEL_VER=4.4','FIRMWARE_ROOTFS_VER=198.9','FIRMWARE_BUILDS_VER=TEST',
          'CROSS_COMPILE=mipsel-linux-uclibc-']
 result=subprocess.check_output(command,text=True,stderr=subprocess.STDOUT)
 assert str(romfs)+' '+str(images/'ramdisk') in result
 assert str(images/'WR1200JS_4.4.198.9-TEST.trx') in result
 assert 'mipsel-linux-uclibc-objcopy' in result
 assert str(trunk/'linux-4.4.x/vmlinux') in result
 assert str(trunk/'romfs') not in result and str(trunk/'images') not in result
 assert list(images.iterdir())==[] and list(romfs.iterdir())==[]
print('PASS actual pinned vendor make dry-run: isolated SquashFS/kernel/TRX destinations, baseline vmlinux read-only, no baseline ROMFS/images path or output mutation; no real image build')
