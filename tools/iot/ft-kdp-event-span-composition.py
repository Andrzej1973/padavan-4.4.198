"""Prepare producer span guard before native KDP event allocation/case reads."""
def compose(source):
    signature='VOID TYPE_FUNC FT_KDP_EventInform('
    if source.count(signature)!=1:raise ValueError('EventInform definition changed')
    start=source.index(signature);end=source.index('\n}',start)+2
    native=source[start:end]
    anchor='\t/* init event content */\n'
    if 'wr_ft_kdp_event_fits(' in native:raise ValueError('event spans already prepared')
    allocation='\tNdisZeroMemory(&EvtHdr, sizeof(FT_KDP_EVT_HEADER));'
    if native.count(allocation)!=1 or native.count(anchor)!=1:
        raise ValueError('event framing anchors changed')
    # Guard input before switch-specific reads; recheck final EventLen after
    # native switch, which may change event length or payload pointer.
    check='wr_ft_kdp_event_fits(sizeof(((FT_KDP_SIGNAL *)0)->Content),sizeof(FT_KDP_EVT_HEADER),EventLen,pEvent!=NULL)'
    typed='''
 if((EventId==FT_KDP_SIG_FT_ASSOCIATION&&
     (!pEvent||EventLen<sizeof(FT_KDP_EVT_ASSOC)))||
    (EventId==FT_KDP_SIG_FT_REASSOCIATION&&
     (!pEvent||EventLen<sizeof(FT_KDP_EVT_REASSOC)))||
    (EventId==FT_KDP_SIG_KEY_REQ&&!PeerIP&&
     (!pEvent||EventLen<sizeof(FT_KDP_EVT_KEY_ELM))))return;
'''
    native=native.replace(allocation,' if(!'+check+')return;\n'+typed+allocation,1)
    native=native.replace(anchor,' if(!'+check+'){FT_MEM_FREE(pAd,pFtKdp);return;}\n'+anchor,1)
    assignment='\tpFtKdp->Sig = EventId;'
    if native.count(assignment)!=1:raise ValueError('event signal publication changed')
    native=native.replace(assignment,' NdisZeroMemory(pFtKdp,sizeof(*pFtKdp));\n'+assignment,1)
    return source[:start]+native+source[end:]
