#!/usr/bin/env python3
"""Verify U-Boot CRCs and every extracted ROMFS entry in an isolated Padavan TRX."""
import argparse,hashlib,json,runpy,struct,subprocess,tempfile,zlib
from pathlib import Path
snapshot=runpy.run_path(str(Path(__file__).resolve().parent/'stage-candidate-romfs.py'))['snapshot']
def verify(image,romfs,unsquashfs='unsquashfs'):
 data=image.read_bytes()
 if len(data)<64 or struct.unpack_from('>I',data)[0]!=0x27051956:raise ValueError('Expected U-Boot header')
 header=bytearray(data[:64]);hcrc=struct.unpack_from('>I',header,4)[0];header[4:8]=b'\0'*4
 if zlib.crc32(header)&0xffffffff!=hcrc:raise ValueError('Header CRC mismatch')
 size=struct.unpack_from('>I',data,12)[0];crc=struct.unpack_from('>I',data,24)[0]
 if size!=len(data)-64 or zlib.crc32(data[64:])&0xffffffff!=crc:raise ValueError('Payload size/CRC mismatch')
 if data[28:31]!=bytes([5,5,2]):raise ValueError('Expected Linux/MIPS/kernel image')
 offsets=[];start=64
 while True:
  n=data.find(b'hsqs',start)
  if n<0:break
  start=n+4
  if subprocess.run([unsquashfs,'-s','-offset',str(n),str(image)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:offsets.append(n)
 if len(offsets)!=1:raise ValueError('Require one valid embedded SquashFS')
 expected=snapshot(romfs)
 with tempfile.TemporaryDirectory(prefix='wr-iot-trx-extract-') as d:
  root=Path(d)/'root'
  subprocess.run([unsquashfs,'-no-progress','-processors','1','-offset',str(offsets[0]),'-dest',str(root),str(image)],check=True,stdout=subprocess.DEVNULL,umask=0)
  actual=snapshot(root)
  if expected!=actual:
   names=sorted(n for n in expected.keys()|actual.keys() if expected.get(n)!=actual.get(n))
   detail={n:{'expected':expected.get(n),'actual':actual.get(n)} for n in names[:12]}
   raise ValueError('Extracted ROMFS mismatch: '+json.dumps(detail,sort_keys=True))
 return {'image_sha256':hashlib.sha256(data).hexdigest(),'image_bytes':len(data),'uboot_header_crc_verified':True,
         'payload_crc_verified':True,'squashfs_offset':offsets[0],'all_romfs_entries_verified':len(expected),
         'isolated_trx_contents_verified':True,'production_installed':False,'physical_runtime_verified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('image',type=Path);p.add_argument('romfs',type=Path)
 p.add_argument('--unsquashfs',default='unsquashfs');p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 if a.report.exists():raise SystemExit('Report exists')
 a.report.write_text(json.dumps(verify(a.image,a.romfs,a.unsquashfs),indent=2)+'\n')
 print('PASS isolated TRX CRCs and complete extracted ROMFS content/modes/links; physical runtime unverified')
