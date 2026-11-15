/* Internal observation only. Caller retains RTNL plus adapter/Main/ra2/module
 * lifetime for the entire call. No ioctl route or hardware access installed.
 * MacTabLock and transition lock must never be held together. */
#include "precreated-down-reference.h"
static INT wr_iot_precreated_down_observed(PRTMP_ADAPTER ad,PNET_DEV dev,
 unsigned long generation)
{
 ULONG flags=0;int peers,exact;
 if(!ad||!dev||!generation)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 /* Failed allocation/unwind may not have initialized either lock. */
 if(!READ_ONCE(ad->wr_iot_recovery_storage_live))return -EAGAIN;
 if(!IS_MT7603(ad)||ad->ApCfg.BssidNum!=3||
    ad->ApCfg.MBSSID[2].wdev.if_dev!=dev||ad->net_dev==dev||
    netif_running(dev)||netif_running(ad->net_dev))return -EAGAIN;
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 peers=!ad->wr_iot_peer_delete_active&&!ad->wr_iot_peer_close_serial&&
  ad->wr_iot_peer_open_owner.phase==WR_PEER_OPEN_IDLE&&
  !ad->wr_iot_peer_open_owner.active_lease&&wr_iot_precreated_down_peers_current(&ad->wr_iot_peer_table_owner,
  &ad->wr_iot_peer_close_executor);
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 if(!peers)return -EAGAIN;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 exact=!ad->wr_iot_control_users&&!ad->wr_iot_control_poisoned&&
  !ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  !ad->wr_iot_driver_owner.active&&!ad->wr_iot_driver_owner.poisoned&&
  !ad->wr_iot_close_owner.active&&
  wr_iot_precreated_down_reference(&ad->wr_iot_main_recovery,
   &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   ad->net_dev,dev,generation,VIRTUAL_IF_NUM(ad));
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!exact)return -EAGAIN;
 /* A peer owner may have appeared between the disjoint snapshots. Recheck
  * it; success remains a point-in-time observation, never a future lease. */
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 peers=!ad->wr_iot_peer_delete_active&&!ad->wr_iot_peer_close_serial&&
  ad->wr_iot_peer_open_owner.phase==WR_PEER_OPEN_IDLE&&
  !ad->wr_iot_peer_open_owner.active_lease&&wr_iot_precreated_down_peers_current(&ad->wr_iot_peer_table_owner,
  &ad->wr_iot_peer_close_executor);
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 return peers?0:-EAGAIN;
}
