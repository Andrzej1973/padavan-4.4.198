#!/usr/bin/env python3
"""Pin MT BSS-sync ARB read/modify/write to the existing beacon lock."""
import argparse
import hashlib
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('input', type=Path)
p.add_argument('candidate', type=Path)
p.add_argument('fixture', type=Path)
a = p.parse_args()
if len({x.resolve() for x in (a.input, a.candidate, a.fixture)}) != 3 or a.candidate.exists() or a.fixture.exists():
    raise SystemExit('Distinct input and new outputs required')
data = a.input.read_bytes()
blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
if blob != 'a8c0c0ec59c7e51c88296111934597064cf36c4a':
    raise SystemExit('Unreviewed MT ASIC source')
source = data.decode('utf-8')
functions = []
blocks = []
for signature, indent, bit in (
    ('VOID AsicEnableBssSync(RTMP_ADAPTER *pAd, USHORT BeaconPeriod)', '\t', '0x1'),
    ('VOID AsicEnableApBssSync(RTMP_ADAPTER *pAd, USHORT BeaconPeriod)', '    ', '0x2'),
):
    if source.count(signature) != 1:
        raise SystemExit('Changed sync function: '+signature)
    start = source.index(signature)
    end = source.index('\n}', start)+2
    f = source[start:end]
    old = (indent+'RTMP_IO_READ32(pAd, ARB_BCNQCR0, &Value);\n'
           +indent+'Value |= '+bit+';\n'
           +indent+'RTMP_IO_WRITE32(pAd, ARB_BCNQCR0, Value);')
    if f.count(old) != 1:
        raise SystemExit('Changed ARB operation: '+signature)
    new = (indent+'/* Serialize this RMW with secondary BSS open/close/recovery. */\n'
           +indent+'RTMP_SEM_LOCK(&pAd->BcnRingLock);\n'
           +old+'\n'+indent+'RTMP_SEM_UNLOCK(&pAd->BcnRingLock);')
    f = f.replace(old, new, 1)
    source = source[:start]+f+source[end:]
    functions.append((signature, f))
    blocks.append(new)
prefix = r'''#include <assert.h>
#include <stdio.h>
typedef unsigned int UINT32;
typedef struct adapter {int BcnRingLock;} RTMP_ADAPTER;
#define ARB_BCNQCR0 0x200U
static UINT32 arb;
static int locks,unlocks,reads,writes;
#define RTMP_SEM_LOCK(lock) do {assert(!*(lock));*(lock)=1;locks++;} while(0)
#define RTMP_SEM_UNLOCK(lock) do {assert(*(lock));*(lock)=0;unlocks++;} while(0)
#define RTMP_IO_READ32(ad,address,value) do {assert((ad)->BcnRingLock&&(address)==ARB_BCNQCR0);reads++;*(value)=arb;} while(0)
#define RTMP_IO_WRITE32(ad,address,value) do {assert((ad)->BcnRingLock&&(address)==ARB_BCNQCR0);writes++;arb=(value);} while(0)
'''
fixture = prefix
for i, block in enumerate(blocks):
    fixture += f'\nstatic void queue{i}(RTMP_ADAPTER *pAd){{UINT32 Value;\n{block}\n}}\n'
fixture += r'''
int main(void){
 RTMP_ADAPTER ad={0};
 arb=0xa5a50000U;queue0(&ad);
 assert(arb==0xa5a50001U&&locks==1&&unlocks==1&&reads==1&&writes==1&&!ad.BcnRingLock);
 queue1(&ad);
 assert(arb==0xa5a50003U&&locks==2&&unlocks==2&&reads==2&&writes==2&&!ad.BcnRingLock);
 puts("PASS pinned MT BSS sync ARB operations: locked RMW preserves secondary BSS bits");
 return 0;
}
'''
if a.input.read_bytes() != data:
    raise SystemExit('Input changed')
a.candidate.write_text(source, encoding='utf-8')
a.fixture.write_text(fixture, encoding='utf-8')
