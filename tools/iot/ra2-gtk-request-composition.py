"""Bind only the native ra2 AP GROUPKEY REQUEST body to a synchronous lease."""
GUARD='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'


def compose(text):
    if 'wr_iot_ra2_group_request_raw' in text:
        raise ValueError('GTK request binding already installed')
    start=text.index('else if ((peerKeyInfo.Request == 1) && (peerKeyInfo.Error == 0))')
    marker='if (peerKeyInfo.KeyType == GROUPKEY)'
    group=text.index(marker,start)
    brace=text.index('{',group)
    depth=1;end=brace+1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    body='\n'.join(line.rstrip() for line in text[brace+1:end-1].split('\n'))
    if body.count('WPAInstallSharedKey(')!=1 or body.count('wr_assoc_event_entry_current(')!=1:
        raise ValueError('GTK request body/guard changed')
    raw='''
#ifdef CONFIG_AP_SUPPORT
'''+GUARD+'''
#include "ra2-gtk-request-kernel.h"
#endif
static VOID wr_iot_ra2_group_request_raw(RTMP_ADAPTER *pAd,
 MLME_QUEUE_ELEM *Elem,MAC_TABLE_ENTRY *pEntry)
{
 INT i;UCHAR apidx=pEntry->func_tb_idx;
'''+body+'''
}
static VOID wr_iot_ra2_group_request(RTMP_ADAPTER *ad,
 MLME_QUEUE_ELEM *event,MAC_TABLE_ENTRY *entry)
{
'''+GUARD+'''
 /* Receiver BSSID belongs to the immutable queued frame: classifying only
  * the current entry could route a reused ra2 slot through native fallback. */
 if(IS_MT7603(ad)&&((entry&&entry->func_tb_idx==2)||
    (event->MsgLen>=LENGTH_802_11&&
     MAC_ADDR_EQUAL(((PHEADER_802_11)event->Msg)->Addr1,
      ad->ApCfg.MBSSID[2].wdev.bssid)))){
  struct wr_iot_ra2_gtk_request_scope scope;
  if(event->MsgLen<LENGTH_802_11||
     !MAC_ADDR_EQUAL(((PHEADER_802_11)event->Msg)->Addr1,
      ad->ApCfg.MBSSID[2].wdev.bssid))return;
  if(wr_iot_ra2_gtk_request_enter(ad,event,entry,&scope)){
   wr_iot_ra2_group_request_raw(ad,event,entry);
   wr_iot_ra2_gtk_request_leave(ad,&scope);
  }
  return;
 }
#endif
 wr_iot_ra2_group_request_raw(ad,event,entry);
}
#endif
'''
    # The loop index moves with the factored native block; no unused outer i.
    old='\t\t\t\t\tINT\t\ti;\n\t\t\t\t\tUCHAR \tapidx = pEntry->func_tb_idx;\n'
    before=text[:brace]
    at=before.rfind(old)
    if at<start:
        raise ValueError('GTK loop index scope changed')
    before=before[:at]+before[at:].replace(old,'',1)
    text=before+'{\n wr_iot_ra2_group_request(pAd,Elem,pEntry);\n}'+text[end:]
    signature='\nVOID WpaEAPOLKeyAction('
    if text.count(signature)!=1:
        raise ValueError('GTK action definition anchor changed')
    position=text.index(signature)+1
    return text[:position]+raw+text[position:]
