"""Prepare an explicit owned-ticket native RX enqueue clone; never installed.

Requires ledger storage and future consumer cleanup integration before use.
Successful enqueue moves the caller reference under queue lock; any failure
retains the reference in the caller. No MacTabLock acquired under Queue->Lock.
"""


def one(text, old, new, count=1):
    if text.count(old) != count:
        raise ValueError('FT pending enqueue anchor changed: ' + old[:90])
    return text.replace(old, new)


def compose(text):
    if 'wr_ft_pending_enqueue_for_recv' in text:
        raise ValueError('FT pending enqueue already prepared')
    start = text.index('BOOLEAN MlmeEnqueueForRecv(')
    end = text.index('\n}', start)+2
    body = text[start:end]
    body = one(body, 'BOOLEAN MlmeEnqueueForRecv(', 'BOOLEAN wr_ft_pending_enqueue_for_recv(')
    body = one(body, 'IN UCHAR OpMode)',
               'IN UCHAR OpMode,\n IN struct wr_ft_pending_token *wr_ticket)')
    body = one(body, '\tif (!pFrame)', ''' if(!wr_ticket||!wr_ticket->generation||!pFrame||Wcid!=RESERVED_WCID||
  MsgLen<LENGTH_802_11+offsetof(FT_ACTION,Oct)||
  wr_ticket->bss>=pAd->ApCfg.BssidNum||
  wr_ticket->bss>=sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0])||
  !MAC_ADDR_EQUAL(pFrame->Hdr.Addr1,pAd->ApCfg.MBSSID[wr_ticket->bss].wdev.bssid)||
  !MAC_ADDR_EQUAL(pFrame->Hdr.Addr2,wr_ticket->addr))return FALSE;
 {
 const FT_ACTION *wr_action=(const FT_ACTION *)((const unsigned char *)Msg+LENGTH_802_11);
 if(wr_action->Category!=FT_CATEGORY_BSS_TRANSITION||wr_action->Action!=FT_ACTION_BT_REQ||
  !MAC_ADDR_EQUAL(wr_action->StaMac,wr_ticket->addr)||
  !MAC_ADDR_EQUAL(wr_action->TargetApAddr,pFrame->Hdr.Addr1))return FALSE;
 }
\tif (!pFrame)''')
    # This clone transports only pending FT actions. Existing-peer and ordinary
    # traffic keep their original function; no implicit identity recapture.
    capture = 'wr_stamp = wr_assoc_capture(pAd, Machine, MsgLen, Msg, Wcid);'
    body = one(body, capture,
               'if(Machine!=ACTION_STATE_MACHINE||MsgType!=FT_CATEGORY_BSS_TRANSITION)return FALSE;\n'
               ' NdisZeroMemory(&wr_stamp,sizeof(wr_stamp));', 2)
    for queue in ('Queue', 'EAP_Queue'):
        occupied = 'if ('+queue+'->Entry[Tail].Occupied)'
        body = one(body, occupied,
                   'if ('+queue+'->Entry[Tail].Occupied || '+queue+'->Entry[Tail].ft_pending_generation)')
        # Move before Num/Tail/Occupied publication; refusal is side-effect free.
        advance = '\t\t'+queue+'->Tail++;'
        lock='\tNdisAcquireSpinLock(&('+queue+'->Lock));'
        if queue == 'Queue':
            body=one(body,lock,lock+'\n'
                ' if(Queue->wr_ft_pending_closed){NdisReleaseSpinLock(&(Queue->Lock));return FALSE;}')
        else:
            body=one(body,lock,lock+'\n'
                ' if(Machine==ACTION_STATE_MACHINE&&MsgType==FT_CATEGORY_BSS_TRANSITION){'
                'NdisReleaseSpinLock(&(EAP_Queue->Lock));return FALSE;}')
        body = one(body, advance,
                   ' if(!wr_ft_pending_elem_publish(&'+queue+'->Entry[Tail],wr_ticket)){\n'
                   '  NdisReleaseSpinLock(&('+queue+'->Lock));return FALSE;\n }\n'+advance)
    prototype = body[:body.index('{')].rstrip()+';'
    added = '\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-pending-queue.h"\n'+prototype+'\n'+body+'\n#endif\n'
    return text[:end]+added+text[end:], prototype


def queue_fields(header):
    if 'ft_pending_generation' in header:
        raise ValueError('FT pending queue fields already prepared')
    return one(header, '\tULONG Machine;',
               '#ifdef DOT11R_FT_SUPPORT\n'
               ' unsigned int ft_pending_generation,ft_pending_slot,ft_pending_bss;\n'
               ' unsigned char ft_pending_addr[6];\n#endif\n\tULONG Machine;')


def queue_closed_field(header):
    if 'wr_ft_pending_closed' in header:
        raise ValueError('FT pending queue close field already prepared')
    return one(header, '\tMLME_QUEUE_ELEM Entry[MAX_LEN_OF_MLME_QUEUE];',
               '#ifdef DOT11R_FT_SUPPORT\n unsigned int wr_ft_pending_closed;\n#endif\n'
               '\tMLME_QUEUE_ELEM Entry[MAX_LEN_OF_MLME_QUEUE];')


def lifecycle(text):
    """Prepare native metadata init, dispatch release, restart and halt drains."""
    if 'wr_ft_pending_queue_discard_all' in text:
        raise ValueError('FT pending lifecycle already prepared')
    text = one(text, '#include "rt_config.h"',
               '#include "rt_config.h"\n#include "ft-pending-queue.h"')

    # Queue slots persist across ring reuse. Clear only the new sidecar fields
    # at the native point where each slot is initialized.
    start = text.index('NDIS_STATUS MlmeQueueInit(')
    end = text.index('\n}', start)+2
    body = text[start:end]
    body=one(body,'\tQueue->Num\t= 0;',
             '\tQueue->Num\t= 0;\n#ifdef DOT11R_FT_SUPPORT\n Queue->wr_ft_pending_closed=0;\n#endif')
    for q, limit in [('Queue','MAX_LEN_OF_MLME_QUEUE'),('EAP_Queue','MAX_LEN_OF_EAP_QUEUE')]:
        marker='\t\t'+q+'->Entry[i].Occupied = FALSE;'
        if marker in body:
            body=one(body,marker,'\t\twr_ft_pending_elem_init(&'+q+'->Entry[i]);\n'+marker)
    text=text[:start]+body+text[end:]

    # Drain by detaching one token under queue lock, then releasing its ledger
    # reference under MacTabLock after Queue->Lock has been dropped.
    discard=r'''
''' + elem_current_helper() + r'''
static void wr_ft_pending_queue_discard_all(RTMP_ADAPTER *pAd,MLME_QUEUE *queue,
 unsigned int capacity)
{
 unsigned int i;
 for(i=0;i<capacity;i++){
  struct wr_ft_pending_token token={0};
  NdisAcquireSpinLock(&queue->Lock);
  (void)wr_ft_pending_elem_detach(&queue->Entry[i],&token);
  queue->Entry[i].Occupied=FALSE;queue->Entry[i].MsgLen=0;
  NdisReleaseSpinLock(&queue->Lock);
  if(token.generation){
   NdisAcquireSpinLock(&pAd->MacTabLock);
   (void)wr_ft_pending_release_locked(&pAd->wr_ft_pending,&token);
   NdisReleaseSpinLock(&pAd->MacTabLock);
  }
 }
 NdisAcquireSpinLock(&queue->Lock);queue->Num=0;queue->Head=0;queue->Tail=0;
 NdisReleaseSpinLock(&queue->Lock);
}
'''
    # The handler and a candidate's shared halt body both use these helpers.
    # Define them immediately after the queue header, before either caller.
    at=text.index('#include "ft-pending-queue.h"')+len('#include "ft-pending-queue.h"')
    text=text[:at]+'\n#ifdef DOT11R_FT_SUPPORT\n'+discard+'\n#endif\n'+text[at:]

    # A pending ticket stays in Elem through the FT handler. Validate before
    # dispatch; release after every handler or before the stale-drop continue.
    start=text.index('VOID MlmeHandler(');end=text.index('\n}',start)+2
    body=text[start:end]
    anchor='\t\tif (Elem) '
    validate='''
#ifdef DOT11R_FT_SUPPORT
 if(Elem->ft_pending_generation){
  NdisAcquireSpinLock(&pAd->MacTabLock);
  if(!wr_ft_pending_elem_current_locked(pAd,Elem)){
   (void)wr_ft_pending_release_elem_locked(pAd,Elem);
   NdisReleaseSpinLock(&pAd->MacTabLock);
   Elem->Occupied=FALSE;Elem->MsgLen=0;continue;
  }
  NdisReleaseSpinLock(&pAd->MacTabLock);
 }
#endif
'''
    # Avoid nested locking in the stale branch: detach metadata first, release
    # its ledger token while the same MacTabLock remains held.
    validate=validate.replace('   (void)wr_ft_pending_release_elem_locked(pAd,Elem);',
      '   (void)wr_ft_pending_elem_release_locked(pAd,Elem);')
    body=one(body,anchor,validate+anchor)
    anchor='\t\t\tElem->Occupied = FALSE;\n\t\t\tElem->MsgLen = 0;'
    release='''#ifdef DOT11R_FT_SUPPORT
 if(Elem->ft_pending_generation)(void)wr_ft_pending_elem_release(pAd,Elem);
#endif
'''
    body=one(body,anchor,release+anchor)
    text=text[:start]+body+text[end:]

    # Restart only reaches the drain after acquiring bRunning; the early-return
    # path above preserves the currently executing dispatcher's ownership.
    start=text.index('VOID MlmeRestartStateMachine(');end=text.index('\n}',start)+2
    body=text[start:end]
    release='\t\tpAd->Mlme.bRunning = TRUE;\n\t}\n\tNdisReleaseSpinLock(&pAd->Mlme.TaskLock);'
    drain='''
#ifdef DOT11R_FT_SUPPORT
 NdisAcquireSpinLock(&pAd->Mlme.Queue.Lock);
 pAd->Mlme.Queue.wr_ft_pending_closed=1;
 NdisReleaseSpinLock(&pAd->Mlme.Queue.Lock);
 wr_ft_pending_queue_discard_all(pAd,&pAd->Mlme.Queue,MAX_LEN_OF_MLME_QUEUE);
#endif
'''
    body=one(body,release,release+'\n'+drain)
    reopen='''
#ifdef DOT11R_FT_SUPPORT
 NdisAcquireSpinLock(&pAd->Mlme.Queue.Lock);
 pAd->Mlme.Queue.wr_ft_pending_closed=0;
 NdisReleaseSpinLock(&pAd->Mlme.Queue.Lock);
#endif
'''
    tail='\tRTMPResumeMsduTransmission(pAd);'
    body=one(body,tail,tail+'\n'+reopen)
    text=text[:start]+body+text[end:]

    # Some candidate predecessors split the checked and legacy wrappers from
    # their shared halt body. Drain inside that body, after task stop and before
    # queue/lock destruction, so both entry paths receive the same lifecycle.
    halt_signature=('static BOOLEAN wr_iot_mlme_halt_body('
        if 'static BOOLEAN wr_iot_mlme_halt_body(' in text else 'VOID MlmeHalt(')
    start=text.index(halt_signature);end=text.index('\n}',start)+2
    body=text[start:end]
    destroy='MlmeQueueDestroy(&pAd->Mlme.EAP_Queue, &pAd->Mlme.Queue);'
    if body.count(destroy)!=1:
        raise ValueError('FT pending enqueue requires one EAP queue destroy call')
    destroy_at=body.index(destroy)
    anchor_at=body.rfind('#ifdef EAPOL_QUEUE_SUPPORT',0,destroy_at)
    if anchor_at<0 or body.find('#else',anchor_at,destroy_at)>=0:
        raise ValueError('FT pending enqueue requires the guarded EAP queue destroy block')
    drain='''#ifdef DOT11R_FT_SUPPORT
 NdisAcquireSpinLock(&pAd->Mlme.Queue.Lock);
 pAd->Mlme.Queue.wr_ft_pending_closed=1;
 NdisReleaseSpinLock(&pAd->Mlme.Queue.Lock);
 wr_ft_pending_queue_discard_all(pAd,&pAd->Mlme.Queue,MAX_LEN_OF_MLME_QUEUE);
#endif
'''
    body=body[:anchor_at]+drain+body[anchor_at:]
    text=text[:start]+body+text[end:]
    return text


def elem_current_helper():
    return r'''
static inline int wr_ft_pending_elem_current_locked(RTMP_ADAPTER *pAd,
 const MLME_QUEUE_ELEM *elem)
{
 struct wr_ft_pending_token token={0};
 unsigned int i;
 if(!elem||!elem->ft_pending_generation)return 0;
 token.generation=elem->ft_pending_generation;token.slot=elem->ft_pending_slot;
 token.bss=elem->ft_pending_bss;
 for(i=0;i<MAC_ADDR_LEN;i++)token.addr[i]=elem->ft_pending_addr[i];
 return wr_ft_pending_current_locked(&pAd->wr_ft_pending,&token);
}
'''
