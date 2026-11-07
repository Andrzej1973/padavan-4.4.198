#!/usr/bin/env python3
"""Extract and exercise the isolated DMA ring snapshot, without RF claims."""
import argparse
from pathlib import Path


p = argparse.ArgumentParser()
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    raise SystemExit('New fixture output required')
source = (a.candidate / 'common/cmm_data_pci.c').read_text(encoding='utf-8')
signature = 'INT32 WrBeaconDmaOutstanding(RTMP_ADAPTER *pAd, UINT32 BssId)'
if source.count(signature) != 1:
    raise SystemExit('DMA snapshot missing or duplicated')
start = source.index(signature)
end = source.index('\n}', start) + 2
function = source[start:end]
prefix = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef unsigned int UINT32;
typedef unsigned char UCHAR;
typedef int INT32;
#define BCN_RING_SIZE 4
#define MAX_MBSSID_NUM(ad) 3
typedef struct packet {
    union { UINT32 words[2]; UCHAR bytes[8]; } data;
    UINT32 len;
} PACKET, *PNDIS_PACKET;
typedef struct { UINT32 pad; } TMAC_TXD_0;
typedef struct { UINT32 own_mac; } TMAC_TXD_1;
typedef struct { PNDIS_PACKET pNdisPacket, pNextNdisPacket; } RTMP_DMACB;
typedef struct {
    RTMP_DMACB Cell[BCN_RING_SIZE];
    UINT32 TxCpuIdx, TxSwFreeIdx;
} RTMP_BCN_RING;
typedef struct {
    struct { UINT32 BssidNum; } ApCfg;
    RTMP_BCN_RING BcnRing;
    int BcnRingLock;
} RTMP_ADAPTER;
#define RTMP_SEM_LOCK(lock) do { assert(*(lock) == 0); *(lock) = 1; } while (0)
#define RTMP_SEM_UNLOCK(lock) do { assert(*(lock) == 1); *(lock) = 0; } while (0)
#define GET_OS_PKT_LEN(packet) ((packet)->len)
#define GET_OS_PKT_DATAPTR(packet) ((packet)->data.bytes)
'''
tail = r'''
static void set_owner(PACKET *pkt, UINT32 owner)
{
    memset(pkt, 0, sizeof(*pkt));
    pkt->data.words[1] = owner;
    pkt->len = sizeof(pkt->data);
}
int main(void)
{
    RTMP_ADAPTER ad = {0};
    PACKET main_pkt, iot_pkt, other_pkt;
    ad.ApCfg.BssidNum = 3;
    set_owner(&main_pkt, 0);
    set_owner(&iot_pkt, 0x12);
    set_owner(&other_pkt, 0x11);
    assert(WrBeaconDmaOutstanding(&ad, 2) == 0 && !ad.BcnRingLock);
    ad.BcnRing.Cell[0].pNdisPacket = &main_pkt;
    ad.BcnRing.Cell[1].pNdisPacket = &iot_pkt;
    ad.BcnRing.TxCpuIdx = 2;
    assert(WrBeaconDmaOutstanding(&ad, 2) == 1 && !ad.BcnRingLock);
    assert(WrBeaconDmaOutstanding(&ad, 1) == 0 && !ad.BcnRingLock);
    ad.BcnRing.Cell[1].pNdisPacket = &other_pkt;
    assert(WrBeaconDmaOutstanding(&ad, 2) == 0 && !ad.BcnRingLock);
    other_pkt.data.words[1] = 0x22;
    assert(WrBeaconDmaOutstanding(&ad, 2) == -1 && !ad.BcnRingLock);
    other_pkt.data.words[1] = 0x13;
    assert(WrBeaconDmaOutstanding(&ad, 2) == -1 && !ad.BcnRingLock);
    other_pkt.data.words[1] = 0x11;
    other_pkt.len = 2;
    assert(WrBeaconDmaOutstanding(&ad, 2) == -1 && !ad.BcnRingLock);
    other_pkt.len = sizeof(other_pkt.data);
    ad.BcnRing.Cell[1].pNextNdisPacket = &iot_pkt;
    assert(WrBeaconDmaOutstanding(&ad, 2) == -1 && !ad.BcnRingLock);
    ad.BcnRing.Cell[1].pNextNdisPacket = NULL;
    ad.BcnRing.Cell[1].pNdisPacket = NULL;
    assert(WrBeaconDmaOutstanding(&ad, 2) == -1 && !ad.BcnRingLock);
    ad.BcnRing.TxCpuIdx = BCN_RING_SIZE;
    assert(WrBeaconDmaOutstanding(&ad, 2) == -1 && !ad.BcnRingLock);
    assert(WrBeaconDmaOutstanding(&ad, 3) == -1 && !ad.BcnRingLock);
    puts("PASS isolated beacon DMA snapshot: owners, unknowns, ring mismatch, lock release");
    return 0;
}
'''
a.output.write_text(prefix + function + tail, encoding='utf-8')
print('Extracted actual candidate DMA snapshot; host fixture only')
