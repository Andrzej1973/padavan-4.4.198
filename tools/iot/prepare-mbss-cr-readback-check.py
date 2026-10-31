#!/usr/bin/env python3
"""Extract the candidate CR-disable function into a host MMIO fixture.

The fixture verifies control-bit readback only. It cannot model RF silence,
pending RX TxS reports, kernel locking, or the target MIPS register bus.
"""
import argparse
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument('candidate', type=Path, help='generated driver/ap/ap_mbss.c')
parser.add_argument('output', type=Path, help='new host fixture C file')
args = parser.parse_args()
if args.output.exists() or args.output.resolve() == args.candidate.resolve():
    raise SystemExit('Fixture output must be new and distinct')
source = args.candidate.read_text(encoding='utf-8')
signature = 'INT mbss_cr_disable(PNET_DEV pDev)'
if source.count(signature) != 1:
    raise SystemExit('Expected one CR-disable function')
start = source.index(signature)
end = source.index('\n}', start) + 2
function = source[start:end]
for anchor in ('RTMP_IO_READ32(pAd, ARB_BCNQCR0, &Readback);',
               'Readback & (TBTT0_n_INT_EN | PRE_TBTT0_n_INT_EN)',
               'Readback & (0x1U << (BssId + 15))'):
    if function.count(anchor) != 1:
        raise SystemExit('CR-disable readback candidate changed: ' + anchor)

prefix = r'''#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef int INT;
typedef uint32_t UINT32;
typedef unsigned char UCHAR;
typedef int BOOLEAN;
#define TRUE 1
#define FALSE 0
#define HIF_MT 1
#define LPON_SBTOR1 0x100U
#define ARB_BCNQCR0 0x200U
#define SUB_BSSID0_TIME_OFFSET_n_MASK 0x0000ff00U
#define SUB_BSSID0_TIME_OFFSET_n(v) (((UINT32)(v) << 8) & SUB_BSSID0_TIME_OFFSET_n_MASK)
#define TBTT0_n_INT_EN 0x1U
#define PRE_TBTT0_n_INT_EN 0x2U
#define SBSS_TBTT0_TSF0_EN 0x4U
struct adapter {
 struct { int hif_type; } chipCap;
 struct { int BssidNum; struct { struct { int bBcnSntReq; } bcn_buf; } MBSSID[3]; } ApCfg;
 int BcnRingLock;
};
typedef struct adapter *PRTMP_ADAPTER;
typedef struct device { PRTMP_ADAPTER ad; int index; } *PNET_DEV;
static UINT32 lpon[2], arb;
static int held, sticky_tbtt, sticky_queue, writes;
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->ad)
static int RT28xx_MBSS_IdxGet(PRTMP_ADAPTER ad, PNET_DEV dev)
{ assert(ad && dev); return dev->index; }
#define RTMP_SEM_LOCK(lock) ((void)(lock), assert(!held), held = 1)
#define RTMP_SEM_UNLOCK(lock) ((void)(lock), assert(held), held = 0)
static void read_reg(PRTMP_ADAPTER ad, UINT32 address, UINT32 *value)
{
 assert(ad && held && value);
 if (address == ARB_BCNQCR0) *value = arb;
 else { assert(address == LPON_SBTOR1 || address == LPON_SBTOR1 + 4);
        *value = lpon[(address - LPON_SBTOR1) / 4]; }
}
static void write_reg(PRTMP_ADAPTER ad, UINT32 address, UINT32 value)
{
 assert(ad && held); writes++;
 if (address == ARB_BCNQCR0)
  arb = value | (sticky_queue ? (1U << 17) : 0);
 else { assert(address == LPON_SBTOR1 || address == LPON_SBTOR1 + 4);
        if (address == LPON_SBTOR1 + 4 && sticky_tbtt)
         value |= TBTT0_n_INT_EN | PRE_TBTT0_n_INT_EN;
        lpon[(address - LPON_SBTOR1) / 4] = value; }
}
#define RTMP_IO_READ32(ad,address,value) read_reg((ad),(address),(value))
#define RTMP_IO_WRITE32(ad,address,value) write_reg((ad),(address),(value))
'''
suffix = r'''
static void reset(struct adapter *ad, struct device *dev)
{
 memset(ad, 0, sizeof(*ad)); ad->chipCap.hif_type = HIF_MT;
 ad->ApCfg.BssidNum = 3;
 for (int i = 0; i < 3; ++i) ad->ApCfg.MBSSID[i].bcn_buf.bBcnSntReq = TRUE;
 dev->ad = ad; dev->index = 2;
 lpon[0] = TBTT0_n_INT_EN | PRE_TBTT0_n_INT_EN | SBSS_TBTT0_TSF0_EN;
 lpon[1] = lpon[0];
 arb = (1U << 0) | (1U << 16) | (1U << 17);
 sticky_tbtt = sticky_queue = writes = held = 0;
}
int main(void)
{
 struct adapter ad; struct device dev;
 reset(&ad, &dev);
 assert(mbss_cr_disable(&dev) == 0 && !held && writes == 2);
 assert(!ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq);
 assert(ad.ApCfg.MBSSID[1].bcn_buf.bBcnSntReq);
 assert((arb & ((1U << 0) | (1U << 16))) == ((1U << 0) | (1U << 16)));
 assert(!(arb & (1U << 17)) && lpon[0] == 7U);
 assert(!(lpon[1] & (TBTT0_n_INT_EN | PRE_TBTT0_n_INT_EN)));
 reset(&ad, &dev); sticky_tbtt = 1;
 assert(mbss_cr_disable(&dev) == -1 && !held);
 assert(lpon[1] & TBTT0_n_INT_EN);
 reset(&ad, &dev); sticky_queue = 1;
 assert(mbss_cr_disable(&dev) == -1 && !held);
 assert(arb & (1U << 17));
 reset(&ad, &dev); dev.index = 3;
 assert(mbss_cr_disable(&dev) == -1 && !held && !writes);
 for (int i = 0; i < 3; ++i) assert(ad.ApCfg.MBSSID[i].bcn_buf.bBcnSntReq);
 puts("PASS extracted secondary BSS CR readback: success, sticky TBTT/queue, neighbor preservation, invalid index; no RF/TxS proof");
 return 0;
}
'''
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(prefix + function + suffix, encoding='utf-8')
print('Prepared host-only CR readback fixture from generated candidate source')
