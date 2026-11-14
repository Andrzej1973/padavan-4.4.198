"""Transform the reviewed executor only; does not supply arm API/lifetime pins."""
def compose(source):
    def once(old,new):
        nonlocal source
        if source.count(old)!=1:
            raise ValueError('Physical stop executor anchor changed: '+old)
        source=source.replace(old,new,1)
    once('INT result;int accepted,started;', 'INT result;int accepted,started,wr_physical=0;')
    once(' accepted=wr_iot_peer_close_executor_enter(&pAd->wr_iot_peer_close_executor,WR_PEER_CLOSE_LEGACY,0);', ''' if(pAd->wr_iot_physical_stop.phase!=WR_PHYS_STOP_IDLE){
  struct wr_iot_physical_stop_record *r=&pAd->wr_iot_physical_stop;
  if(net_dev!=pAd->net_dev||!wr_iot_peer_close_executor_idle(&pAd->wr_iot_peer_close_executor)||
     !wr_iot_physical_stop_begin(r,r->serial,r->epoch,r->generation,r->nonce,current)){
   NdisReleaseSpinLock(&pAd->MacTabLock);return NDIS_STATUS_FAILURE;
  }
  wr_physical=1;
 }
 accepted=wr_iot_peer_close_executor_enter(&pAd->wr_iot_peer_close_executor,WR_PEER_CLOSE_LEGACY,0);''')
    once(' return accepted?result:NDIS_STATUS_FAILURE;\n}\nINT wr_iot_drv_close_checked', ''' if(wr_physical){
  struct wr_iot_physical_stop_record *r=&pAd->wr_iot_physical_stop;
  NdisAcquireSpinLock(&pAd->MacTabLock);
  accepted=wr_iot_physical_stop_finish(r,r->serial,r->epoch,r->generation,
   r->nonce,current,accepted&&result==NDIS_STATUS_SUCCESS,
   &pAd->wr_iot_peer_close_executor,&pAd->wr_iot_peer_table_owner,
   pAd->wr_iot_peer_legacy_close_state);
  NdisReleaseSpinLock(&pAd->MacTabLock);
 }
 return accepted?result:NDIS_STATUS_FAILURE;
}
INT wr_iot_drv_close_checked''')
    once(' accepted=wr_iot_peer_close_executor_enter(&pAd->wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,ticket->serial);', ' if(pAd->wr_iot_physical_stop.phase!=WR_PHYS_STOP_IDLE){\n  NdisReleaseSpinLock(&pAd->MacTabLock);return NDIS_STATUS_FAILURE;\n }\n accepted=wr_iot_peer_close_executor_enter(&pAd->wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,ticket->serial);')
    # Finish observation in the same critical section as executor leave. A
    # release/reacquire gap could otherwise admit a new open before recording.
    once(' NdisReleaseSpinLock(&pAd->MacTabLock);\n if(wr_physical){\n  struct wr_iot_physical_stop_record *r=&pAd->wr_iot_physical_stop;\n  NdisAcquireSpinLock(&pAd->MacTabLock);', ' if(wr_physical){\n  struct wr_iot_physical_stop_record *r=&pAd->wr_iot_physical_stop;')
    once('  NdisReleaseSpinLock(&pAd->MacTabLock);\n }\n return accepted?result:NDIS_STATUS_FAILURE;', ' }\n NdisReleaseSpinLock(&pAd->MacTabLock);\n return accepted?result:NDIS_STATUS_FAILURE;')
    once('INT result;int accepted,started,wr_physical=0;',
         'INT result;int accepted,started,wr_physical=0;unsigned long long wr_completed_epoch=0;')
    once(' result=wr_iot_legacy_close_body(pAdSrc,net_dev);',
         ' result=wr_iot_legacy_close_body(pAdSrc,net_dev);\n if(wr_physical)wr_completed_epoch=wr_iot_physical_stop_completion_epoch(pAd);')
    once('accepted=wr_iot_physical_stop_finish(r,r->serial,r->epoch,r->generation,',
         'accepted=wr_iot_physical_stop_finish_at_epoch(r,r->serial,r->epoch,r->generation,')
    once('   pAd->wr_iot_peer_legacy_close_state);',
         '   pAd->wr_iot_peer_legacy_close_state,wr_completed_epoch);')
    # Mandatory adapter binding must sample actual completed-close state under
    # transition lock outside MacTabLock; no stored-epoch fallback supplied.
    source='static unsigned long long wr_iot_physical_stop_completion_epoch(RTMP_ADAPTER *);\n'+source
    return source

def compose_open_dispatch(source):
    """Block new main-open dispatch while an exact stop attempt remains owned."""
    anchor=' if (request->device!=pAd->net_dev) goto done;'
    if source.count(anchor)!=1 or 'wr_iot_physical_stop.phase' in source:
        raise ValueError('Physical stop main-open anchor changed')
    return source.replace(anchor,anchor+'\n if(pAd->wr_iot_physical_stop.phase!=WR_PHYS_STOP_IDLE) goto done;',1)

def compose_adapter(header,initialization):
    """Add dormant adapter-owned storage at the existing fresh-only init point.

    Not an arm endpoint. Never invoke on UserCfgInit, reopen or recovery.
    """
    include='#include "peer-close-executor.h"'
    field='struct wr_iot_peer_close_executor wr_iot_peer_close_executor;'
    init='wr_iot_peer_close_executor_init(&pAd->wr_iot_peer_close_executor);'
    marker='/* Last nonfailing initialization before adapter publication. */'
    if (header.count(include)!=1 or header.count(field)!=1 or
        initialization.count(init)!=1 or initialization.count(marker)!=1 or
        'struct wr_iot_physical_stop_record wr_iot_physical_stop;' in header):
        raise ValueError('Physical-stop adapter storage anchor changed')
    # Confirm the existing init is in the fresh adapter publication block.
    begin=initialization.index(marker)
    end=initialization.index('wr_iot_radio_transition_init(&pAd->wr_iot_transition);',begin)
    if not begin<initialization.index(init)<end:
        raise ValueError('Close executor no longer initialized before publication')
    header=header.replace(include,include+'\n#include "physical-stop-record.h"\n#include "physical-stop-lifetime.h"',1)
    header=header.replace(field,field+'\n struct wr_iot_physical_stop_record wr_iot_physical_stop;\n struct wr_iot_physical_stop_lifetime wr_iot_physical_lifetime;',1)
    initialization=initialization.replace(init,init+'\n\t\tNdisZeroMemory(&pAd->wr_iot_physical_stop,sizeof(pAd->wr_iot_physical_stop));\n\t\tNdisZeroMemory(&pAd->wr_iot_physical_lifetime,sizeof(pAd->wr_iot_physical_lifetime));',1)
    return header,initialization

def compose_retirement(work,join):
    """Retirement gates read only transition-lock-owned physical lifetime."""
    def once(text,old,new):
        if text.count(old)!=1 or 'wr_iot_physical_stop_lifetime_blocks' in text:
            raise ValueError('Physical lifetime retirement anchor changed')
        return text.replace(old,new,1)
    work=once(work,' if(ad && (ad->wr_iot_idle_probe.active ||',
              ' if(ad && (wr_iot_physical_stop_lifetime_blocks(&ad->wr_iot_physical_lifetime) ||\n     ad->wr_iot_idle_probe.active ||')
    join=once(join,' if(ad->wr_iot_idle_probe.active ||',
              ' if(wr_iot_physical_stop_lifetime_blocks(&ad->wr_iot_physical_lifetime) ||\n    ad->wr_iot_idle_probe.active ||')
    return work,join
