/* Prepared over-air AUTH callback boundary. Caller owns MacTabLock and the
 * dequeued element plus adapter/BSS lifetime. Never recapture generation. */
#ifndef WR_FT_AUTH_PEER_SCOPE_H
#define WR_FT_AUTH_PEER_SCOPE_H
#include "ft-peer-generation.h"
#include "ft-pending-queue.h"
static inline int wr_ft_auth_event_matches(RTMP_ADAPTER *ad,
 const MLME_QUEUE_ELEM *event,unsigned int bss,const unsigned char *addr)
{
 const FRAME_802_11 *frame;const unsigned char *auth;
 if(!ad||!event||!addr)return 0;
 if(event->Machine!=AP_AUTH_STATE_MACHINE||event->MsgType!=APMT2_PEER_AUTH_REQ||
    event->MsgLen<LENGTH_802_11+6||event->MsgLen>sizeof(event->Msg)||
    bss>=ad->ApCfg.BssidNum||
    bss>=sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0]))return 0;
 frame=(const FRAME_802_11 *)event->Msg;
 auth=(const unsigned char *)event->Msg+LENGTH_802_11;
 if(frame->Hdr.FC.Type!=FC_TYPE_MGMT||frame->Hdr.FC.SubType!=SUBTYPE_AUTH||
    !MAC_ADDR_EQUAL(frame->Hdr.Addr1,ad->ApCfg.MBSSID[bss].wdev.bssid)||
    !MAC_ADDR_EQUAL(frame->Hdr.Addr2,addr)||auth[0]!=2||auth[1]||
    auth[2]!=1||auth[3]||auth[4]||auth[5])return 0;
 return 1;
}
static inline int wr_ft_auth_existing_enter_locked(RTMP_ADAPTER *ad,
 const MLME_QUEUE_ELEM *event,unsigned int bss,const unsigned char *addr,
 struct wr_ft_peer_scope *scope,MAC_TABLE_ENTRY **entry)
{
 struct wr_ft_peer_stamp stamp={0};unsigned int i;
 if(!entry)return 0;
 *entry=NULL;
 if(!ad||!event||!addr||!scope||scope->active||event->ft_pending_generation||!event->assoc_gen||
    event->assoc_wcid==RESERVED_WCID||event->assoc_wcid>=MAX_LEN_OF_MAC_TABLE||
    event->Wcid!=event->assoc_wcid)return 0;
 if(!wr_ft_auth_event_matches(ad,event,bss,addr))return 0;
 stamp.generation=event->assoc_gen;stamp.wcid=event->assoc_wcid;stamp.bss=bss;
 for(i=0;i<MAC_ADDR_LEN;i++){
  if(event->assoc_addr[i]!=addr[i])return 0;
  stamp.addr[i]=event->assoc_addr[i];
 }
 if(!wr_ft_peer_enter_locked(ad,&stamp,scope))return 0;
 *entry=&ad->MacTab.Content[stamp.wcid];return 1;
}

/* Snapshot the queue-owned ticket only: no ref duplication or ownership move. */
static inline int wr_ft_auth_pending_current_locked(RTMP_ADAPTER *ad,
 const MLME_QUEUE_ELEM *event,unsigned int bss,const unsigned char *addr,
 struct wr_ft_pending_token *ticket)
{
 struct wr_ft_pending_token captured={0};
 if(!ticket||ticket->generation||!wr_ft_auth_event_matches(ad,event,bss,addr)||
    event->assoc_gen||event->assoc_wcid!=RESERVED_WCID||event->Wcid!=RESERVED_WCID||
    !wr_ft_pending_elem_snapshot(event,&captured))return 0;
 if(captured.bss!=bss||!MAC_ADDR_EQUAL(captured.addr,addr)||
    !wr_ft_pending_current_locked(&ad->wr_ft_pending,&captured))return 0;
 *ticket=captured;return 1;
}
#endif
