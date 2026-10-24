#!/usr/bin/env python3
"""Stage lock-coordinated PDMA reset gate transitions, without full-reset lock."""
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
if blob != '82db49fa1822a51268d76f23bce94d886f4d50d6':
    raise SystemExit('Unreviewed PCI MAC source')
source = data.decode('utf-8')
signature = 'VOID PDMAResetAndRecovery(RTMP_ADAPTER *pAd)'
if source.count(signature) != 1:
    raise SystemExit('Changed PDMA reset signature')
start = source.index(signature)
end = source.index('\n}', start)+2
f = source[start:end]
old_set = '\tRTMP_SET_FLAG(pAd, fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET);'
old_clear = '\tRTMP_CLEAR_FLAG(pAd, fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET);'
if f.count(old_set) != 1 or f.count(old_clear) != 1:
    raise SystemExit('Changed reset gate transitions')
begin = '''\t/* Linearize the reset gate with final beacon kickout. */
\tRTMP_IRQ_LOCK(&pAd->BcnRingLock, IrqFlags);
'''+old_set+'''
\tRTMP_IRQ_UNLOCK(&pAd->BcnRingLock, IrqFlags);'''
finish = '''\tRTMP_IRQ_LOCK(&pAd->BcnRingLock, IrqFlags);
'''+old_clear+'''
\tRTMP_IRQ_UNLOCK(&pAd->BcnRingLock, IrqFlags);'''
f = f.replace(old_set, begin, 1).replace(old_clear, finish, 1)
candidate = source[:start]+f+source[end:]
fixture = r'''#include <assert.h>
#include <stdio.h>
typedef unsigned long ULONG;
typedef struct adapter {int BcnRingLock;unsigned int flags;} RTMP_ADAPTER;
#define fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET 0x00800000U
#define RTMP_SET_FLAG(ad,flag) do {assert((ad)->BcnRingLock);(ad)->flags|=(flag);} while(0)
#define RTMP_CLEAR_FLAG(ad,flag) do {assert((ad)->BcnRingLock);(ad)->flags&=~(flag);} while(0)
#define RTMP_IRQ_LOCK(lock,flags) do {(flags)=0;assert(!*(lock));*(lock)=1;locks++;} while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do {(void)(flags);assert(*(lock));*(lock)=0;unlocks++;} while(0)
static int locks,unlocks,kicks;
static void kickout(RTMP_ADAPTER *pAd){
 assert(!pAd->BcnRingLock);pAd->BcnRingLock=1;
 if(!(pAd->flags&fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET))kicks++;
 pAd->BcnRingLock=0;
}
static void begin_reset(RTMP_ADAPTER *pAd){ULONG IrqFlags=0;
'''+begin+r'''
}
static void end_reset(RTMP_ADAPTER *pAd){ULONG IrqFlags=0;
'''+finish+r'''
}
int main(void){
 RTMP_ADAPTER ad={0};
 kickout(&ad);assert(kicks==1);
 begin_reset(&ad);assert(ad.flags==fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET);
 kickout(&ad);assert(kicks==1);
 end_reset(&ad);assert(!ad.flags);
 kickout(&ad);assert(kicks==2);
 assert(!ad.BcnRingLock&&locks==2&&unlocks==2);
 puts("PASS pinned PDMA reset gate: lock-coordinated start/end excludes modeled kickout");
 return 0;
}
'''
if a.input.read_bytes() != data:
    raise SystemExit('Input changed')
a.candidate.write_text(candidate, encoding='utf-8')
a.fixture.write_text(fixture, encoding='utf-8')
