#!/usr/bin/env python3
"""Synthetic image mutations for embedded IoT/HNAT policy, not runtime proof."""
from pathlib import Path
import lzma,runpy,struct
inspect=runpy.run_path(str(Path(__file__).with_name('hwnat-image-policy.py')))['inspect_image']

def dtb(devices=None,lan='eth2',wan='eth3',model='YouHua WR1200JS',duplicate=False):
    names=['model','mtketh-lan','mtketh-wan','ext-devices']
    strings=b'';offsets={}
    for name in names:offsets[name]=len(strings);strings+=name.encode()+b'\0'
    def pad(b):return b+b'\0'*((-len(b))%4)
    def node(name):return struct.pack('>I',1)+pad(name.encode()+b'\0')
    def prop(name,value):
        b='\0'.join(value).encode()+b'\0'
        return struct.pack('>III',3,len(b),offsets[name])+pad(b)
    body=node('')+prop('model',[model])+node('hnat@1e100000')
    body+=prop('mtketh-lan',[lan])+prop('mtketh-wan',[wan])
    body+=prop('ext-devices',devices if devices is not None else ['ra0','rai0','usb0'])
    if duplicate:body+=prop('mtketh-lan',[lan])
    body+=struct.pack('>III',2,2,9)
    return struct.pack('>10I',0xd00dfeed,56+len(body)+len(strings),56,56+len(body),40,17,16,0,len(strings),len(body))+b'\0'*16+body+strings

def image(kernel):
    payload=lzma.compress(kernel,format=lzma.FORMAT_ALONE)
    return struct.pack('>7I4B32s',0x27051956,0,0,len(payload),0,0,0,5,5,2,3,b'WR1200JS')+payload

def reject(data,label):
    try:inspect(data)
    except (ValueError,lzma.LZMAError,UnicodeError):pass
    else:raise AssertionError('Accepted '+label)

assert inspect(image(dtb()))['external_devices']==['ra0','rai0','usb0']
for dev in ['ra2','rai2','br-iot']:
    reject(image(dtb(['ra0','rai0',dev])),dev+' admitted to offload')
for devices in [['ra0'],['rai0'],['ra0','rai0','ra0'],['ra0','rai0','x'*16],[]]:
    reject(image(dtb(devices)),'invalid external device list')
reject(image(dtb(lan='eth3',wan='eth2')),'swapped physical ports')
reject(image(dtb(model='another board')),'foreign board')
reject(image(dtb(duplicate=True)),'duplicate property')
reject(image(dtb()+b'\0'+b'\0'*3+dtb()),'ambiguous two DTBs')
reject(image(dtb()+b'\0'*4+dtb(model='another board')),'ambiguous foreign DTB')
reject(image(b'no device tree'),'missing DTB')
reject(image(dtb())[:-5],'truncated kernel stream')
reject(b'bad header','invalid uImage')
malformed=bytearray(dtb());struct.pack_into('>I',malformed,12,0xffffffff)
reject(image(malformed),'out-of-bounds strings')
malformed=bytearray(dtb());struct.pack_into('>I',malformed,8,40)
reject(image(malformed),'invalid structure block')
malformed=bytearray(dtb());struct.pack_into('>I',malformed,16,41)
reject(image(malformed),'misaligned reservation map')
# Resource refusal uses actual parser without allocating a huge kernel fixture.
parse=runpy.run_path(str(Path(__file__).with_name('hwnat-image-policy.py')))['fdt_properties']
try:parse(b'\0'*(2*1024*1024+1))
except ValueError as exc:assert 'inspection limit' in str(exc)
else:raise AssertionError('Oversized DTB accepted')
# Replace root/hnat path with a deeply nested, otherwise valid tree.
malformed=bytearray(dtb())
extra=struct.pack('>I',1)+b'x\0\0\0'
body=bytes(malformed[56:struct.unpack_from('>I',malformed,12)[0]])
body=body[:8]+extra*65+struct.pack('>I',2)*65+body[8:]
strings=bytes(malformed[struct.unpack_from('>I',malformed,12)[0]:])
header=bytearray(malformed[:56]);struct.pack_into('>I',header,4,56+len(body)+len(strings));struct.pack_into('>I',header,12,56+len(body));struct.pack_into('>I',header,36,len(body))
reject(image(header+body+strings),'deep node nesting')
print('PASS embedded HNAT image policy: valid fixture, IoT exclusion, Main preservation, mapping, malformed/truncated/ambiguous refusal; synthetic only')
