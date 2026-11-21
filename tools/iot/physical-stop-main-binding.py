"""Bind retained ARM identity at actual Main recovery continuation entry.

Pure reviewed source transform; separate installer/endpoint integration needed.
"""
def compose(source):
    marker='static int wr_iot_main_recovery_execute('
    if source.count(marker)!=1:
        raise ValueError('ambiguous Main recovery worker')
    start=source.index(marker);end=source.index('\n}',start)+2
    body=source[start:end]
    anchor=' if (wr_iot_main_close_continue_checked(adapter, net_dev, generation,'
    if body.count(anchor)!=1 or 'wr_iot_physical_stop_lifetime_capture_main' in body:
        raise ValueError('changed/already-bound Main continuation')
    guard=''' /* Bind existing recovery ownership before claiming the physical record.
  * Locks stay disjoint; cancellation wins or RUNNING wins under MacTabLock. */
 {
  int physical_armed;
  struct wr_iot_physical_stop_request physical_request={0};
  unsigned long long physical_prior_serial=0;
  RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
  physical_armed=adapter->wr_iot_physical_lifetime.active;
  bound = 1;
  if (physical_armed) {
   struct wr_iot_radio_ticket physical_ticket;
   record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
                                 WDEV_NUM_MAX + 1, net_dev, generation);
   bound = wr_iot_physical_stop_lifetime_capture_main(
     &adapter->wr_iot_physical_lifetime,
     adapter->wr_iot_physical_lifetime.serial, owner,
     &adapter->wr_iot_transition, record, &physical_ticket);
   physical_request=adapter->wr_iot_physical_lifetime.arm_request;
   physical_prior_serial=adapter->wr_iot_physical_lifetime.arm_record_serial;
  }
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  if (!bound) goto retain;
  if (physical_armed) {
   struct wr_iot_physical_stop_record *physical=&adapter->wr_iot_physical_stop;
   struct wr_iot_physical_stop_pins *pins=&adapter->wr_iot_physical_pins;
   RTMP_IRQ_LOCK(&adapter->MacTabLock, flags);
   bound=physical_request.action==WR_STOP_ARM&&pins->module==1&&pins->task&&
    pins->device==net_dev&&physical_prior_serial!=~0ULL&&
    physical->serial==physical_prior_serial+1&&
    physical->open_token==physical_request.open_token&&
    physical->closed_serial==physical_request.closed_serial&&
    wr_iot_physical_stop_matches(physical,physical->serial,physical_request.epoch,
      physical_request.generation,physical_request.nonce,pins->task);
   if(bound&&physical->phase==WR_PHYS_STOP_ARMED)
    bound=wr_iot_physical_stop_begin(physical,physical->serial,
      physical_request.epoch,physical_request.generation,
      physical_request.nonce,pins->task);
   else if(bound)bound=physical->phase==WR_PHYS_STOP_RUNNING;
   RTMP_IRQ_UNLOCK(&adapter->MacTabLock, flags);
   if (!bound) goto retain;
  }
 }
'''
    body=body.replace(anchor,guard+anchor,1)
    return source[:start]+body+source[end:]

def compose_reset(source):
    """Existing transition lock protects both reset admission and ARM lifetime."""
    anchors={
      ' if(pAd->wr_iot_transition.reset_pending)':
      ' if(!wr_iot_physical_stop_lifetime_blocks(&pAd->wr_iot_physical_lifetime) &&\n    pAd->wr_iot_transition.reset_pending)',
      ' wr_iot_radio_request_reset_kind(&pAd->wr_iot_transition,kind);':
      ' if(!wr_iot_physical_stop_lifetime_blocks(&pAd->wr_iot_physical_lifetime))\n  wr_iot_radio_request_reset_kind(&pAd->wr_iot_transition,kind);',
    }
    if 'wr_iot_physical_stop_lifetime_blocks' in source:
        raise ValueError('reset lifetime already bound')
    for old,new in anchors.items():
        if source.count(old)!=1:
            raise ValueError('changed reset admission anchor')
        source=source.replace(old,new,1)
    return source

def compose_raw_free(source):
    """Extend the existing cold/live direct-free fence; no puts under locks."""
    if 'wr_iot_physical_terminal' in source:
        raise ValueError('physical raw-free fence already installed')
    old=' ready=!ad->wr_iot_registration_inflight &&'
    if source.count(old)!=1:
        raise ValueError('changed raw-free admission')
    source=source.replace(old,' ready=!ad->wr_iot_physical_lifetime.active &&\n  !ad->wr_iot_physical_rebind_probe.active &&\n  !ad->wr_iot_registration_inflight &&',1)
    source='#include "physical-stop-terminal.inc"\n'+source
    old=' RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);\n return ready;'
    new=''' RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(ready){
  struct wr_iot_physical_stop_terminal terminal={0},empty={0};
  RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
  ready=ad->wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE&&
   !ad->wr_iot_physical_stop.task&&!ad->wr_iot_physical_pins.module&&
   !ad->wr_iot_physical_pins.task&&!ad->wr_iot_physical_pins.device&&
   !ad->wr_iot_physical_pending_pins.module&&
   !ad->wr_iot_physical_pending_pins.task&&!ad->wr_iot_physical_pending_pins.device;
  if(ready){terminal=ad->wr_iot_physical_terminal;ad->wr_iot_physical_terminal=empty;}
  RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
  if(terminal.owner)wr_iot_physical_stop_terminal_clear(&terminal);
 }
 return ready;'''
    if source.count(old)!=1:
        raise ValueError('changed raw-free return')
    return source.replace(old,new,1)
