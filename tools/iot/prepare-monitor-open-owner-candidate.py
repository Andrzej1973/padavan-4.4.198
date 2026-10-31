#!/usr/bin/env python3
"""Bind monitor non-first open and identity in an isolated MT76x3 tree."""

import argparse
import hashlib
import shutil
from pathlib import Path


PROFILE_SHA256 = "762bedf782bbf61c14d3ee95087a95864b511d7f8359d5832410e92057f4a3b0"
SNIFFER_SHA256 = "45a7ad61e18a9322cb5895eb327a671b99a0000b59941f5d9b58ce421c3ac44a"
START = b"INT Monitor_VirtualIF_Open(PNET_DEV dev_p)"
END = b"INT Monitor_VirtualIF_Close(PNET_DEV dev_p)"

OPEN = r'''INT Monitor_VirtualIF_Open(PNET_DEV dev_p)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record;
 unsigned long generation=0;
 ULONG flags;
 int admitted,up=0,sniff_attempted=0,sniff_ok=0,finished,ready,owned,retain_pin=1;
 if(!dev_p)return -1;
 RT_MOD_INC_USE_COUNT();
 adapter=RTMP_OS_NETDEV_GET_PRIV(dev_p);
 if(!adapter){RT_MOD_DEC_USE_COUNT();return -1;}
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 /* Until physical first-open recovery is checked, require a radio owner. */
 admitted=VIRTUAL_IF_NUM(adapter)>0 &&
  wr_iot_aux_open_reserve(&adapter->wr_iot_transition,
   adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev_p,WR_REF_FAMILY_MONITOR,
   VIRTUAL_IF_NUM(adapter),&ticket,&generation);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!admitted){RT_MOD_DEC_USE_COUNT();return -1;}
 up=VIRTUAL_IF_UP_CLAIM(adapter,dev_p,&ticket,generation)==0;
 if(up){
  sniff_attempted=1;
  sniff_ok=RTMP_COM_IoctlHandle(adapter,NULL,CMD_RTPRIV_IOCTL_SNIFF_OPEN,
                               0,dev_p,0)==NDIS_STATUS_SUCCESS;
 }
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find(adapter->wr_iot_interface_refs,
                            WDEV_NUM_MAX+1,dev_p,generation);
 finished=wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,
                              up&&sniff_ok);
 ready=wr_iot_aux_open_accepted(&adapter->wr_iot_transition,&ticket,finished);
 owned=ready&&up&&sniff_ok&&record&&
  wr_iot_ref_complete_aux_open(record,dev_p,generation,ticket.serial,
                               1,1,1,1,1,&retain_pin);
 if(!owned&&record&&record->phase==WR_REF_RESERVED)
  wr_iot_ref_complete_aux_open(record,dev_p,generation,ticket.serial,
                               1,1,up&&ready,sniff_attempted,
                               sniff_ok&&ready,&retain_pin);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 wake_up_all(&adapter->wr_iot_ticket_wait);
 if(!owned)return -1; /* retain pin until checked recovery */
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 RT_MOD_HNAT_REG(dev_p);
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
    profile = (source / "os/linux/rt_profile.c").read_bytes()
    sniffer = (source / "sniffer/sniffer_radiotap.c").read_bytes()
    if hashlib.sha256(profile).hexdigest() != PROFILE_SHA256 or \
            hashlib.sha256(sniffer).hexdigest() != SNIFFER_SHA256:
        parser.error("monitor sources differ from reviewed candidate")
    if profile.count(START) != 1 or profile.count(END) != 1:
        parser.error("monitor wrapper anchors are ambiguous")
    begin, end = profile.index(START), profile.index(END)
    changed = profile[:begin] + OPEN + profile[end:]
    include = b'#include "rt_config.h"'
    if changed.count(include) != 1:
        parser.error("monitor include anchor changed")
    changed = changed.replace(include, include + b'\n#include "virtual-open-claim.h"')
    old = b'\t}\n\n\treturn TRUE;\n}\n\n\nBOOLEAN Monitor_Close('
    if sniffer.count(old) != 1:
        parser.error("monitor identity return anchor changed")
    fixed = sniffer.replace(old,
        b'\t\treturn TRUE;\n\t}\n\n\treturn FALSE;\n}\n\n\nBOOLEAN Monitor_Close(')
    shutil.copytree(source, output)
    (output / "os/linux/rt_profile.c").write_bytes(changed)
    (output / "sniffer/sniffer_radiotap.c").write_bytes(fixed)
    print(f"Prepared isolated monitor open owner: {output}")


if __name__ == "__main__":
    main()
