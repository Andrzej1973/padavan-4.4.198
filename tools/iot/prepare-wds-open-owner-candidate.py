#!/usr/bin/env python3
"""Bind WDS non-first open to the isolated shared radio owner."""

import argparse
import hashlib
import shutil
from pathlib import Path


SOURCE_SHA256 = "65d2bc7586b4754e65fb70e47800489b175c520d3bf76c1f44af0a613927687f"
START = b"INT WdsVirtualIF_open(PNET_DEV dev)"
END = b"INT WdsVirtualIF_close(PNET_DEV dev)"

OPEN = r'''INT WdsVirtualIF_open(PNET_DEV dev)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record;
 unsigned long generation=0;
 ULONG flags;
 int admitted,up,finished,ready,owned,retain_pin=1;
 if(!dev)return -1;
 RT_MOD_INC_USE_COUNT();
 adapter=RTMP_OS_NETDEV_GET_PRIV(dev);
 if(!adapter){RT_MOD_DEC_USE_COUNT();return -1;}
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 /* WDS may not become the first physical radio owner until its separate
  * first-open recovery path exists. The main interface normally owns it. */
 admitted=VIRTUAL_IF_NUM(adapter)>0 &&
  wr_iot_aux_open_reserve(&adapter->wr_iot_transition,
   adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,WR_REF_FAMILY_WDS,
   VIRTUAL_IF_NUM(adapter),&ticket,&generation);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!admitted){RT_MOD_DEC_USE_COUNT();return -1;}
 up=VIRTUAL_IF_UP_CLAIM(adapter,dev,&ticket,generation)==0;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find(adapter->wr_iot_interface_refs,
                            WDEV_NUM_MAX+1,dev,generation);
 finished=wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,up);
 ready=wr_iot_aux_open_accepted(&adapter->wr_iot_transition,&ticket,finished);
 owned=ready&&up&&record&&
  wr_iot_ref_complete_aux_open(record,dev,generation,ticket.serial,
                               0,1,1,0,0,&retain_pin);
 if(!owned&&record&&record->phase==WR_REF_RESERVED)
  wr_iot_ref_complete_aux_open(record,dev,generation,ticket.serial,
                               0,1,up&&ready,0,0,&retain_pin);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 wake_up_all(&adapter->wr_iot_ticket_wait);
 /* After a virtual-UP attempt, retain the module pin on any uncertain
  * outcome. Failed ndo_open has no guaranteed ndo_stop callback. */
 if(!owned)return -1;
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 RT_MOD_HNAT_REG(dev);
#endif
 RTMP_OS_NETDEV_START_QUEUE(dev);
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
    path = source / "ap/ap_wds_inf.c"
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        parser.error("WDS source differs from the reviewed candidate")
    if data.count(START) != 1 or data.count(END) != 1:
        parser.error("WDS wrapper anchors are ambiguous")
    begin, end = data.index(START), data.index(END)
    if end <= begin:
        parser.error("unexpected WDS wrapper order")
    shutil.copytree(source, output)
    shutil.copyfile(Path(__file__).with_name("radio-transition.h"),
                    output / "include/radio-transition.h")
    changed = data[:begin] + OPEN + data[end:]
    anchor = b'/*#include "rt_config.h" */'
    if changed.count(anchor) != 1:
        parser.error("WDS include anchor changed")
    changed = changed.replace(anchor,
                              b'#include "rt_config.h"\n#include "virtual-open-claim.h"')
    (output / "ap/ap_wds_inf.c").write_bytes(changed)
    print(f"Prepared isolated WDS open owner: {output}")


if __name__ == "__main__":
    main()
