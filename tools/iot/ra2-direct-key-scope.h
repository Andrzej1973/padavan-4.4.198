/* Prepared synchronous scope; not yet installed at the ioctl call site.
 * Caller pins adapter lifetime and zero-initializes a private linear scope.
 * No user-copy, key I/O or callbacks occur under the transition/table locks. */
#ifndef WR_IOT_RA2_DIRECT_KEY_SCOPE_H
#define WR_IOT_RA2_DIRECT_KEY_SCOPE_H
#include "ra2-association-owner.h"
#include "ra2-rekey-admission.h"
#include "ra2-direct-key-peer.h"
struct wr_ra2_direct_key_scope {
 RTMP_ADAPTER *owner;
 unsigned int active;
 struct wr_ra2_assoc_ticket key;
 struct wr_ra2_rekey_peer_scope peers;
};
static inline int wr_ra2_direct_key_release_control(RTMP_ADAPTER *ad,
 struct wr_ra2_direct_key_scope *scope,int failed)
{
 ULONG flags=0;int valid;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 valid=scope->owner==ad&&scope->key.active&&scope->key.key&&
  scope->key.owner==&ad->wr_ra2_assoc_owner&&
  ad->wr_ra2_assoc_owner.key_active==1&&
  ad->wr_ra2_assoc_owner.key_serial==scope->key.serial&&
  ad->wr_iot_ra2_key_active==1&&ad->wr_iot_control_users;
 if(!valid){ad->wr_iot_control_poisoned=1;}
 else if(!wr_ra2_assoc_leave(&ad->wr_ra2_assoc_owner,&scope->key)){
  ad->wr_iot_control_poisoned=1;valid=0;
 }else{
  ad->wr_iot_ra2_key_active=0;--ad->wr_iot_control_users;
  scope->owner=NULL;scope->active=0;
  if(failed)ad->wr_iot_control_poisoned=1;
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return valid&&!failed;
}
static inline int wr_ra2_direct_key_enter(RTMP_ADAPTER *ad,
 struct wr_ra2_direct_key_scope *scope)
{
 ULONG flags=0;int admitted=0;
 if(!ad||!scope||scope->active||scope->owner||scope->key.active||scope->peers.active)return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(ad->ApCfg.BssidNum==3&&!ad->wr_iot_ra2_key_active){
  admitted=wr_iot_ra2_rekey_admit(&ad->wr_iot_driver_owner,
   &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   ad->net_dev,ad->ApCfg.MBSSID[2].wdev.if_dev,VIRTUAL_IF_NUM(ad),
   &ad->wr_iot_control_users,&ad->wr_iot_control_poisoned,
   ad->wr_iot_boot_active||ad->wr_iot_boot_failed||
   ad->wr_iot_close_owner.active||ad->wr_iot_closed_probe.active);
  if(admitted&&!wr_ra2_assoc_enter(&ad->wr_ra2_assoc_owner,&scope->key,1)){
   --ad->wr_iot_control_users;admitted=0;
   if(ad->wr_ra2_assoc_owner.poisoned)ad->wr_iot_control_poisoned=1;
  }
  if(admitted){ad->wr_iot_ra2_key_active=1;scope->owner=ad;scope->active=1;}
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!admitted)return 0;
 if(!wr_ra2_rekey_peers_enter(ad,&scope->peers)){
  (void)wr_ra2_direct_key_release_control(ad,scope,0);return 0;
 }
 return 1;
}
static inline int wr_ra2_direct_key_leave(RTMP_ADAPTER *ad,
 struct wr_ra2_direct_key_scope *scope)
{
 int valid;ULONG flags=0;
 if(!ad||!scope)return 0;
 /* Refuse foreign or drifted ownership before touching any peer reservation. */
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 valid=scope->active&&scope->owner==ad&&scope->key.active&&scope->key.key&&
  scope->key.owner==&ad->wr_ra2_assoc_owner&&
  ad->wr_ra2_assoc_owner.key_active==1&&
  ad->wr_ra2_assoc_owner.key_serial==scope->key.serial&&
  ad->wr_iot_ra2_key_active==1&&ad->wr_iot_control_users;
 if(!valid)ad->wr_iot_control_poisoned=1;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!valid)return 0;
 valid=wr_ra2_rekey_peers_leave(ad,&scope->peers);
 return wr_ra2_direct_key_release_control(ad,scope,!valid);
}
#endif
