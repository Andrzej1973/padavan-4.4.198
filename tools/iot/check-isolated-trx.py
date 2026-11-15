"""Real SquashFS and U-Boot-shaped fixtures exercise full extraction gate."""
from pathlib import Path
import runpy,tempfile,subprocess,struct,zlib
here=Path(__file__).resolve().parent
verify=runpy.run_path(str(here/'verify-isolated-trx.py'))['verify']
with tempfile.TemporaryDirectory(prefix='wr-trx-full-check-') as d:
 root=Path(d);romfs=root/'romfs';(romfs/'sbin').mkdir(parents=True)
 (romfs/'sbin/rc').write_bytes(b'target fixture');(romfs/'sbin/rc').chmod(0o755);(romfs/'init').symlink_to('sbin/rc')
 (romfs/'etc').mkdir();(romfs/'etc/settings').write_bytes(b'preserve')
 fs=root/'root.sqfs';subprocess.run(['mksquashfs',str(romfs),str(fs),'-noappend','-no-progress','-processors','1'],check=True,stdout=subprocess.DEVNULL)
 payload=b'kernel fixture'+fs.read_bytes();header=bytearray(64)
 struct.pack_into('>IIIIIII',header,0,0x27051956,0,0,len(payload),0x81001000,0x81001000,zlib.crc32(payload)&0xffffffff)
 header[28:32]=bytes([5,5,2,3]);struct.pack_into('>I',header,4,zlib.crc32(header)&0xffffffff)
 image=root/'fixture.trx';good=bytes(header)+payload;image.write_bytes(good)
 r=verify(image,romfs);assert r['isolated_trx_contents_verified'] and not r['physical_runtime_verified']
 for fault in range(4):
  damaged=bytearray(good)
  if fault==0:damaged[4]^=1
  if fault==1:damaged[65]^=1
  image.write_bytes(damaged)
  if fault==2:(romfs/'etc/settings').write_bytes(b'changed')
  if fault==3:(romfs/'sbin/rc').chmod(0o644)
  try:verify(image,romfs)
  except ValueError:pass
  else:raise AssertionError('Corrupted image/content accepted')
  (romfs/'etc/settings').write_bytes(b'preserve');(romfs/'sbin/rc').chmod(0o755)
print('PASS isolated TRX gate: actual SquashFS extraction, complete entry/mode/link comparison, header/payload CRC and unrelated-setting/mode corruption refusals; synthetic kernel/header, not firmware acceptance')
