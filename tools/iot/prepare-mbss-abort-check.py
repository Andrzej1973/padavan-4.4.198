#!/usr/bin/env python3
"""Compile the isolated vendor MBSS_AbortOpen body with bounded host mocks."""

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output must be a new file")
    source = (args.candidate / "ap/ap_mbss.c").read_text(encoding="utf-8")
    start = source.index("INT MBSS_AbortOpen(PNET_DEV pDev)")
    end = source.index("INT MBSS_Close(PNET_DEV pDev)", start)
    body = source[start:end]
    if body.count("BndStrg_SetInfFlags(") != 0:
        parser.error("abort body must not clear band-wide Band Steering readiness")
    fixture = r'''#include <assert.h>
#include <stdio.h>
#define BAND_STEERING 1
#define FALSE 0
typedef int INT;
typedef unsigned int UINT32;
typedef void *PBND_STRG_CLI_TABLE;
struct bss {struct {int bBcnSntReq;} bcn_buf; int wdev;};
struct adapter {struct {UINT32 BssidNum;int BandSteering;
 struct bss MBSSID[3];} ApCfg; int BcnRingLock;};
typedef struct adapter *PRTMP_ADAPTER;
struct device {PRTMP_ADAPTER ad;INT index;};
typedef struct device *PNET_DEV;
static int held;
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->ad)
#define RTMP_SEM_LOCK(lock) do {(void)(lock);assert(!held);held=1;}while(0)
#define RTMP_SEM_UNLOCK(lock) do {(void)(lock);assert(held);held=0;}while(0)
static INT RT28xx_MBSS_IdxGet(PRTMP_ADAPTER ad,PNET_DEV dev)
{assert(ad&&dev&&!held);return dev->index;}
''' + body + r'''
int main(void){
 struct adapter ad={0};struct device dev={&ad,2};
 ad.ApCfg.BssidNum=3;ad.ApCfg.BandSteering=1;
 ad.ApCfg.MBSSID[0].bcn_buf.bBcnSntReq=1;
 ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
 assert(MBSS_AbortOpen(&dev)==0&&!held&&
        !ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq&&
        ad.ApCfg.MBSSID[0].bcn_buf.bBcnSntReq);
 ad.ApCfg.BandSteering=0;ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
 assert(MBSS_AbortOpen(&dev)==0&&!held);
 dev.index=0;assert(MBSS_AbortOpen(&dev)==-1);
 puts("PASS extracted MBSS abort: IoT beacon cleared, main beacon preserved");
 return 0;
}
'''
    args.output.write_text(fixture, encoding="utf-8")
    print(f"Extracted MBSS abort body: {args.output}")


if __name__ == "__main__":
    main()
