"""Prepare over-air FT AUTH RX provenance, layered over an existing RX path."""
from pathlib import Path
import runpy


def compose(text,active_prototype,pending_prototype):
    if 'wr_ft_auth_rx_pending' in text:
        raise ValueError('FT AUTH RX already prepared')
    signature='BOOLEAN MlmeEnqueueForRecv('
    start=text.index(signature);end=text.index('\n}',start)+2
    native=text[start:end]
    declaration=native[:native.index('{')]
    # Reuse the established bounded BSS lookup/ticket transfer template.
    base=runpy.run_path(str(Path(__file__).with_name('ft-rx-generation-composition.py')))
    template=base['compose'](declaration+'{\n return FALSE;\n}',active_prototype,pending_prototype)
    at=template.index(signature)
    wrapper=template[at:template.index('\n}',at)+2]
    old='''(wr_frame->Hdr.FC.SubType==SUBTYPE_ACTION||
     wr_frame->Hdr.FC.SubType==SUBTYPE_ACTION_NO_ACK)&&
    *((const UCHAR *)Msg+LENGTH_802_11)==FT_CATEGORY_BSS_TRANSITION'''
    if wrapper.count(old)!=1:raise ValueError('FT AUTH RX outer template changed')
    wrapper=wrapper.replace(old,'''wr_frame->Hdr.FC.SubType==SUBTYPE_AUTH&&
    *((const UCHAR *)Msg+LENGTH_802_11)==2''')
    begin=wrapper.index('  PFT_ACTION wr_action;')
    finish=wrapper.index('  for(wr_apidx=',begin)
    wrapper=wrapper[:begin]+'''  const UCHAR *wr_auth=(const UCHAR *)Msg+LENGTH_802_11;
  if(MsgLen<LENGTH_802_11+6)return FALSE;
  if(wr_auth[1])return FALSE;
  if(wr_auth[2]!=1||wr_auth[3])goto wr_ft_auth_rx_fallback;
  if(wr_auth[4]||wr_auth[5])return FALSE;
'''+wrapper[finish:]
    old='''if(!wr_seen&&wr_action->Action==FT_ACTION_BT_REQ&&
     MAC_ADDR_EQUAL(wr_action->TargetApAddr,wr_frame->Hdr.Addr1))'''
    if wrapper.count(old)!=1:raise ValueError('FT AUTH RX pending template changed')
    wrapper=wrapper.replace(old,'if(!wr_seen)')
    wrapper=wrapper.replace('\n#endif\n return wr_ft_native_mlme_enqueue_for_recv',
      '\nwr_ft_auth_rx_fallback:\n#endif\n return wr_ft_native_mlme_enqueue_for_recv',1)
    wrapper=wrapper.replace('wr_ft_rx_pending','wr_ft_auth_rx_pending')
    wrapper=wrapper.replace('wr_ft_mlme_enqueue_for_recv','wr_ft_auth_mlme_enqueue_for_recv')
    wrapper=wrapper.replace('wr_ft_pending_enqueue_for_recv','wr_ft_auth_pending_enqueue_for_recv')
    wrapper=wrapper.replace('wr_ft_native_mlme_enqueue_for_recv','wr_ft_auth_native_mlme_enqueue_for_recv')
    renamed=native.replace(signature,'static BOOLEAN wr_ft_auth_native_mlme_enqueue_for_recv(',1)
    includes='\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-peer-generation.h"\n#include "ft-pending-queue.h"\n'+active_prototype+'\n'+pending_prototype+'\n#endif\n'
    return text[:start]+renamed+includes+wrapper+text[end:]
