#!/usr/bin/env python3
"""Bind AP-client non-first open in a new isolated MT76x3 tree."""

import argparse
import hashlib
import shutil
from pathlib import Path


SOURCE_SHA256 = "9bc1229e731dc5d44e4f6cbf95564579626a71afeb6e0f3d2419549eec4c8f49"
START = b"INT ApCli_VirtualIF_Open(PNET_DEV dev_p)"
END = b"INT ApCli_VirtualIF_Close(PNET_DEV dev_p)"

OPEN = r'''INT ApCli_VirtualIF_Open(PNET_DEV dev_p)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record;
 unsigned long generation=0;
 ULONG flags;
 int admitted,up=0,apcli_attempted=0,apcli_ok=0,finished,ready,owned,retain_pin=1;
 if(!dev_p)return -1;
 RT_MOD_INC_USE_COUNT();
 adapter=RTMP_OS_NETDEV_GET_PRIV(dev_p);
 if(!adapter){RT_MOD_DEC_USE_COUNT();return -1;}
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 /* Physical first-open recovery is unresolved; require an existing owner. */
 admitted=VIRTUAL_IF_NUM(adapter)>0 &&
  wr_iot_aux_open_reserve(&adapter->wr_iot_transition,
   adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev_p,WR_REF_FAMILY_APCLI,
   VIRTUAL_IF_NUM(adapter),&ticket,&generation);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!admitted){RT_MOD_DEC_USE_COUNT();return -1;}
 up=VIRTUAL_IF_UP_CLAIM(adapter,dev_p,&ticket,generation)==0;
 if(up){
  apcli_attempted=1;
  apcli_ok=RTMP_AP_IoctlHandle(adapter,NULL,CMD_RTPRIV_IOCTL_APC_OPEN,
                              0,dev_p,0)==NDIS_STATUS_SUCCESS;
 }
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find(adapter->wr_iot_interface_refs,
                            WDEV_NUM_MAX+1,dev_p,generation);
 finished=wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,
                              up&&apcli_ok);
 ready=wr_iot_aux_open_accepted(&adapter->wr_iot_transition,&ticket,finished);
 owned=ready&&up&&apcli_ok&&record&&
  wr_iot_ref_complete_aux_open(record,dev_p,generation,ticket.serial,
                               1,1,1,1,1,&retain_pin);
 if(!owned&&record&&record->phase==WR_REF_RESERVED)
  wr_iot_ref_complete_aux_open(record,dev_p,generation,ticket.serial,
                               1,1,up&&ready,apcli_attempted,
                               apcli_ok&&ready,&retain_pin);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 wake_up_all(&adapter->wr_iot_ticket_wait);
 /* APC_OPEN may fail after mutating the adapter. Failed ndo_open has no
  * guaranteed stop callback, so keep the pin for checked recovery. */
 if(!owned)return -1;
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 RT_MOD_HNAT_REG(dev_p);
#endif
#ifdef MTFWD
 RTMP_OS_NETDEV_CARRIER_OFF(dev_p);
#endif
 return 0;
}

'''.encode()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if output.exists() or output == source or source in output.parents or output in source.parents:
        parser.error("output must be a new separate directory")
    path = source / "ap/ap_apcli_inf.c"
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        parser.error("AP-client source differs from the reviewed candidate")
    if data.count(START) != 1 or data.count(END) != 1:
        parser.error("AP-client wrapper anchors are ambiguous")
    begin, end = data.index(START), data.index(END)
    if end <= begin:
        parser.error("unexpected AP-client wrapper order")
    changed = data[:begin] + OPEN + data[end:]
    include = b'#include "rt_os_net.h"'
    if changed.count(include) != 1:
        parser.error("AP-client include anchor changed")
    changed = changed.replace(include,
                              include + b'\n#include "rt_config.h"\n#include "virtual-open-claim.h"')
    shutil.copytree(source, output)
    (output / "ap/ap_apcli_inf.c").write_bytes(changed)
    print(f"Prepared isolated AP-client open owner: {output}")


if __name__ == "__main__":
    main()
