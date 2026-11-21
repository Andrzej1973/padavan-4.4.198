"""Prepare exact-stamp over-air FT AUTH enqueue; no RX/callback activation."""
from pathlib import Path
import runpy


def compose(text):
    name='wr_ft_auth_mlme_enqueue_for_recv'
    if name in text:
        raise ValueError('FT AUTH enqueue already prepared')
    base=runpy.run_path(str(Path(__file__).with_name('ft-enqueue-generation-composition.py')))
    preview,_=base['compose'](text)
    start=preview.rindex('BOOLEAN wr_ft_mlme_enqueue_for_recv(')
    end=preview.index('\n}',start)+2
    body=preview[start:end]
    body=body.replace('wr_ft_mlme_enqueue_for_recv',name)
    old='MsgLen<LENGTH_802_11+offsetof(FT_ACTION,Oct)'
    if body.count(old)!=1:raise ValueError('FT AUTH minimum-length anchor changed')
    body=body.replace(old,'MsgLen<LENGTH_802_11+6')
    if body.count('if(!wr_expected')!=1:raise ValueError('FT AUTH null guard changed')
    body=body.replace('if(!wr_expected','if(!pFrame||!wr_expected',1)
    classifier='Machine!=ACTION_STATE_MACHINE||MsgType!=FT_CATEGORY_BSS_TRANSITION'
    if body.count(classifier)!=2:raise ValueError('FT AUTH classifier anchors changed')
    body=body.replace(classifier,'Machine!=AP_AUTH_STATE_MACHINE||MsgType!=APMT2_PEER_AUTH_REQ')
    anchor='\tif (!pFrame)'
    if body.count(anchor)!=1:raise ValueError('FT AUTH frame anchor changed')
    body=body.replace(anchor,''' {
 const unsigned char *auth=(const unsigned char *)Msg+LENGTH_802_11;
 /* Wire authentication algorithm 2, transaction 1; little-endian fields. */
 if(auth[0]!=2||auth[1]||auth[2]!=1||auth[3]||auth[4]||auth[5])return FALSE;
 }
'''+anchor,1)
    prototype=body[:body.index('{')].rstrip()+';'
    addition='\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-peer-generation.h"\n'+prototype+'\n'+body+'\n#endif\n'
    start=text.index('BOOLEAN MlmeEnqueueForRecv(')
    end=text.index('\n}',start)+2
    return text[:end]+addition+text[end:],prototype


def compose_retry(text):
    """Clone native AUTH enqueue with immutable preauth retry identity."""
    name='wr_ft_auth_retry_enqueue_for_recv'
    if name in text:raise ValueError('FT AUTH retry enqueue already prepared')
    preview,_=compose(text)
    start=preview.rindex('BOOLEAN wr_ft_auth_mlme_enqueue_for_recv(')
    body=preview[start:preview.index('\n}',start)+2]
    body=body.replace('wr_ft_auth_mlme_enqueue_for_recv',name)
    body=body.replace('const struct wr_ft_peer_stamp *wr_expected',
                      'const struct wr_ft_preauth_identity *wr_expected')
    body=body.replace('wr_expected->addr','wr_expected->mac')
    body=body.replace('!wr_expected->generation||',
                      '!wr_expected->generation||!wr_expected->serial||',1)
    for queue in ('Queue','EAP_Queue'):
        anchor='wr_assoc_publish(&'+queue+'->Entry[Tail], &wr_stamp);'
        if anchor in body:
            # Slot ownership checked by native code before this point. The
            # stamp is prevalidated; clear old sidecar before exact publication.
            body=body.replace(anchor,anchor+'\n'
              ' wr_ft_preauth_elem_clear(&'+queue+'->Entry[Tail]);\n'
              ' (void)wr_ft_preauth_elem_publish(&'+queue+'->Entry[Tail],wr_expected);')
    check='!MAC_ADDR_EQUAL(pFrame->Hdr.Addr1,pAd->ApCfg.MBSSID[wr_expected->bss].wdev.bssid)'
    if body.count(check)!=2:raise ValueError('FT AUTH retry BSSID anchors changed')
    body=body.replace(check,check+'||\n'
      '  !MAC_ADDR_EQUAL(pFrame->Hdr.Addr1,wr_expected->bssid)')
    prototype=body[:body.index('{')].rstrip()+';'
    addition='\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-preauth-queue.h"\n'+prototype+'\n'+body+'\n#endif\n'
    start=text.index('BOOLEAN MlmeEnqueueForRecv(');end=text.index('\n}',start)+2
    return text[:end]+addition+text[end:],prototype


def compose_pending(text):
    name='wr_ft_auth_pending_enqueue_for_recv'
    if name in text:raise ValueError('FT AUTH pending enqueue already prepared')
    module=runpy.run_path(str(Path(__file__).with_name('ft-pending-enqueue-composition.py')))
    preview,_=module['compose'](text)
    start=preview.rindex('BOOLEAN wr_ft_pending_enqueue_for_recv(')
    body=preview[start:preview.index('\n}',start)+2]
    body=body.replace('wr_ft_pending_enqueue_for_recv',name)
    body=body.replace('MsgLen<LENGTH_802_11+offsetof(FT_ACTION,Oct)',
      'MsgLen<LENGTH_802_11+6')
    start=body.index(' {\n const FT_ACTION *wr_action=')
    end=body.index('\n }\n\tif (!pFrame)',start)+len('\n }')
    body=body[:start]+''' {
 const unsigned char *auth=(const unsigned char *)Msg+LENGTH_802_11;
 if(auth[0]!=2||auth[1]||auth[2]!=1||auth[3]||auth[4]||auth[5])return FALSE;
 }'''+body[end:]
    body=body.replace('ACTION_STATE_MACHINE','AP_AUTH_STATE_MACHINE')
    body=body.replace('FT_CATEGORY_BSS_TRANSITION','APMT2_PEER_AUTH_REQ')
    prototype=body[:body.index('{')].rstrip()+';'
    added='\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-pending-queue.h"\n'+prototype+'\n'+body+'\n#endif\n'
    start=text.index('BOOLEAN MlmeEnqueueForRecv(');end=text.index('\n}',start)+2
    return text[:end]+added+text[end:],prototype
