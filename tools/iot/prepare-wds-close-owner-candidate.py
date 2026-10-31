#!/usr/bin/env python3
"""Stage a non-last WDS checked close in a separate MT76x3 tree."""

import argparse
import hashlib
import shutil
from pathlib import Path


SOURCE_SHA256 = "3e170ab35e7ae89c93bca00ab4da932cdcb9769c3946658fcbe40570da7c93a7"
START = b"INT WdsVirtualIF_close(PNET_DEV dev)"
END = b"VOID RT28xx_WDS_Remove(VOID *pAd)"

CLOSE = r'''INT WdsVirtualIF_close(PNET_DEV dev)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record;
 unsigned long generation=0;
 ULONG flags;
 int admitted,ret,consumed=0;
 if(!dev)return -1;
 adapter=RTMP_OS_NETDEV_GET_PRIV(dev);
 if(!adapter)return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 admitted=wr_iot_aux_close_reserve(&adapter->wr_iot_transition,
  adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,WR_REF_FAMILY_WDS,
  VIRTUAL_IF_NUM(adapter),&ticket,&generation);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!admitted)return -1; /* retain pin; last-close needs physical owner */

 RTMP_OS_NETDEV_STOP_QUEUE(dev);
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 RT_MOD_HNAT_DEREG(dev);
#endif
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find(adapter->wr_iot_interface_refs,
                            WDEV_NUM_MAX+1,dev,generation);
 if(!record||record->phase!=WR_REF_CLOSING||
    record->close_serial!=ticket.serial||
    adapter->wr_iot_transition.busy!=WR_RADIO_AUX_CLOSE||
    adapter->wr_iot_transition.serial!=ticket.serial){
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
  return -1; /* owner must reconcile prior queue/HNAT effects */
 }
 record->close_stage=1;
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);

 ret=wr_iot_virtual_down_checked(adapter,&ticket);
 if(ret!=NDIS_STATUS_SUCCESS)return -1; /* retain ticket, record and pin */
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 consumed=wr_iot_aux_close_finalize_after_down(&adapter->wr_iot_transition,
  adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation,&ticket,1,
  VIRTUAL_IF_NUM(adapter));
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!consumed)return -1; /* no safe replay without checked recovery owner */
 wake_up_all(&adapter->wr_iot_ticket_wait);
 RT_MOD_DEC_USE_COUNT();
 return 0;
}

/* Called only by a future retained recovery owner with a netdev/adapter pin.
 * It cannot be scheduled from ndo_stop until worker teardown is implemented. */
INT WdsVirtualIF_close_retry(PNET_DEV dev)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 unsigned long generation=0;
 ULONG flags;
 int admitted,ret,consumed=0;
 if(!dev)return -1;
 adapter=RTMP_OS_NETDEV_GET_PRIV(dev);
 if(!adapter)return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 admitted=wr_iot_aux_close_retry_unmutated_down(&adapter->wr_iot_transition,
  adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,WR_REF_FAMILY_WDS,
  VIRTUAL_IF_NUM(adapter),&ticket,&generation);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!admitted)return -1;
 ret=wr_iot_virtual_down_checked(adapter,&ticket);
 if(ret!=NDIS_STATUS_SUCCESS){
  RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
  wr_iot_aux_close_retry_release(&adapter->wr_iot_transition,
   adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation,&ticket);
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
  return -1;
 }
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 consumed=wr_iot_aux_close_finalize_after_down(&adapter->wr_iot_transition,
  adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation,&ticket,3,
  VIRTUAL_IF_NUM(adapter));
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!consumed)return -1; /* retained owner must reconcile partial completion */
 wake_up_all(&adapter->wr_iot_ticket_wait);
 RT_MOD_DEC_USE_COUNT();
 return 0;
}

/* Recovery owner calls this only after DOWN was already verified and it
 * holds adapter/netdev lifetime. It must never repeat vendor DOWN. */
INT WdsVirtualIF_close_complete(PNET_DEV dev)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 unsigned long generation=0;
 ULONG flags;
 int admitted,consumed;
 if(!dev)return -1;
 adapter=RTMP_OS_NETDEV_GET_PRIV(dev);
 if(!adapter)return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 admitted=wr_iot_aux_close_claim_after_down(&adapter->wr_iot_transition,
  adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,WR_REF_FAMILY_WDS,
  VIRTUAL_IF_NUM(adapter),&ticket,&generation);
 consumed=admitted&&wr_iot_aux_close_finalize_after_down(
  &adapter->wr_iot_transition,adapter->wr_iot_interface_refs,
  WDEV_NUM_MAX+1,dev,generation,&ticket,5,VIRTUAL_IF_NUM(adapter));
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!consumed)return -1;
 wake_up_all(&adapter->wr_iot_ticket_wait);
 RT_MOD_DEC_USE_COUNT();
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
        parser.error("WDS source differs from reviewed open candidate")
    if data.count(START) != 1 or data.count(END) != 1:
        parser.error("WDS close anchors are ambiguous")
    begin, end = data.index(START), data.index(END)
    changed = data[:begin] + CLOSE + data[end:]
    include = b'#include "virtual-open-claim.h"'
    if changed.count(include) != 1:
        parser.error("WDS claimed include changed")
    changed = changed.replace(include,include+b'\n#include "aux-close-claim.h"')
    shutil.copytree(source, output)
    shutil.copyfile(Path(__file__).with_name("aux-close-claim.h"),
                    output / "include/aux-close-claim.h")
    shutil.copyfile(Path(__file__).with_name("interface-reference.h"),
                    output / "include/interface-reference.h")
    shutil.copyfile(Path(__file__).with_name("radio-transition.h"),
                    output / "include/radio-transition.h")
    (output / "ap/ap_wds_inf.c").write_bytes(changed)
    print(f"Prepared isolated non-last WDS close: {output}")


if __name__ == "__main__":
    main()
