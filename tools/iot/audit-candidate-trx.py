#!/usr/bin/env python3
"""Independently inspect downloaded isolated candidate TRX and selected ROMFS files.

Does not flash, execute MIPS code or establish complete unchanged-ROMFS proof.
"""
import argparse,hashlib,json,struct,subprocess,tempfile,zlib
from pathlib import Path,PurePosixPath
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('artifact',type=Path);p.add_argument('--revision',required=True)
p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=a.artifact.resolve(strict=True)
def read(name):return json.loads((root/name).read_text())
def safe_relative(name):
 path=PurePosixPath(name)
 if not name or path.is_absolute() or '..' in path.parts or '\\' in name:
  raise ValueError('Unsafe artifact path: '+name)
 return name
image_report=read('isolated-image-verification.json');stage=read('isolated-romfs-stage.json')
pair=read('paired-image-inputs.json');classic=read('isolated-classic-config.json')
assert image_report['source_revision']==stage['source_revision']==pair['source_revision']==a.revision
name=safe_relative(image_report['candidate_image']);assert len(PurePosixPath(name).parts)==1
image=root/'isolated-image'/name;data=image.read_bytes();digest=hashlib.sha256(data).hexdigest()
assert digest==image_report['sha256']==classic['image_sha256'] and len(data)==image_report['bytes']
assert len(data)>=64 and data[:4]==bytes.fromhex('27051956')
header=bytearray(data[:64]);stored_header_crc=struct.unpack_from('>I',header,4)[0];header[4:8]=bytes(4)
assert zlib.crc32(header)&0xffffffff==stored_header_crc
assert struct.unpack_from('>I',data,12)[0]==len(data)-64
assert zlib.crc32(data[64:])&0xffffffff==struct.unpack_from('>I',data,24)[0]
assert data[28:31]==bytes([5,5,2]) # Linux, MIPS, kernel image.
# WR1200JS partition gate is fixed independently of the downloaded report.
assert len(data)<=16187392
files={**stage['replacement_sha256'],**classic['sha256']}
for name in files:safe_relative(name)
# Bind each embedded replacement to the actual separately linked artifact.
for entry in pair['files'].values():
 path=root/safe_relative(entry['source']);blob=path.read_bytes()
 assert hashlib.sha256(blob).hexdigest()==entry['sha256'] and len(blob)==entry['bytes']
for name,expected in pair['input_sha256'].items():
 assert hashlib.sha256((root/safe_relative(name)).read_bytes()).hexdigest()==expected
entries={}
with tempfile.TemporaryDirectory(prefix='wr-candidate-trx-audit-') as td:
 temp=Path(td);offsets=[];pos=64
 while True:
  pos=data.find(b'hsqs',pos)
  if pos<0:break
  check=subprocess.run(['unsquashfs','-s','-offset',str(pos),str(image)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  if not check.returncode:offsets.append(pos)
  pos+=4
 assert len(offsets)==1
 dest=temp/'root'
 subprocess.run(['unsquashfs','-no-progress','-processors','1','-offset',str(offsets[0]),'-dest',str(dest),str(image),*files],stdout=subprocess.DEVNULL,check=True)
 for name,expected in files.items():
  path=dest/name;assert path.is_file() and not path.is_symlink()
  blob=path.read_bytes();assert hashlib.sha256(blob).hexdigest()==expected
  entry={'sha256':expected,'bytes':len(blob)}
  if blob[:4]==b'\x7fELF':
   assert blob[:6]==b'\x7fELF\x01\x01' and struct.unpack_from('<H',blob,18)[0]==8
   entry['elf32_le_mips']=True
  entries[name]=entry
 module=stage['module_destination']
 assert entries[module]['sha256']==read('ra2-no-host-module/target-result.json')['module_sha256']
 for item in pair['files'].values():assert item['sha256'] in {entry['sha256'] for entry in entries.values()}
 board=temp/'board.json'
 verifier=Path(__file__).resolve().parents[2]/'overlay/padavan-4.4/scripts/verify-wr1200js-image.py'
 subprocess.run(['python3',str(verifier),str(image),'--report',str(board)],check=True,stdout=subprocess.DEVNULL)
 board_result=json.loads(board.read_text())
report={'revision':a.revision,'image_sha256':digest,'image_bytes':len(data),
 'remaining_partition_bytes':16187392-len(data),'header_and_payload_crc_verified':True,
 'squashfs_offset':offsets[0],'selected_embedded_files':entries,
 'linked_pair_files_and_input_hashes_verified':True,'board_checks':board_result,
 'scope':'Actual selected ROMFS bytes and linked-artifact integrity; not full ROMFS/source correctness or device acceptance',
 'production_promoted':False,'runtime_verified':False}
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
print('Independent candidate TRX CRC/size, selected ROMFS/MIPS and linked-pair hashes: PASS')
