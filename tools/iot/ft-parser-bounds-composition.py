"""Prepare bounded native FT action parsing; not producer-installed yet."""
def one(text,old,new,count=1):
    if text.count(old)!=count:raise ValueError('FT bounds anchor changed: '+old[:80])
    return text.replace(old,new)

def compose(source):
    if 'wr_iot_ft_request_ies_admitted' in source:raise ValueError('FT parser bounds already installed')
    text=one(source,'#include "rt_config.h"',
      '#include "rt_config.h"\n#include "ft-request-ie-admission.h"\n#include "ft-action-bounds.h"')
    start=text.index('static VOID FT_ReqActionParse(',text.index('static VOID FT_ReqActionParse(')+1)
    end=text.index('\n}',start)+2;body=text[start:end]
    body=one(body,'\tPEID_STRUCT eid_ptr;', '\tPEID_STRUCT eid_ptr;\n unsigned int remaining=Len;')
    anchor='\tNdisZeroMemory(pFtInfo, sizeof(FT_INFO));'
    body=one(body,anchor,anchor+'\n if(!wr_iot_ft_request_ies_admitted(Ptr,Len))return;')
    body=one(body,'while(((UCHAR*)eid_ptr + eid_ptr->Len + 1) < ((PUCHAR)Ptr + Len))',
      'while(remaining>=2)')
    advance='eid_ptr = (PEID_STRUCT)((UCHAR*)eid_ptr + 2 + eid_ptr->Len);'
    body=one(body,advance,'remaining -= 2 + eid_ptr->Len;\n        '+advance)
    # RIC view is exactly remaining bytes, not one byte beyond the input.
    body=one(body,'- (UCHAR*)eid_ptr + 1;', '- (UCHAR*)eid_ptr;')
    text=text[:start]+body+text[end:]
    start=text.index('VOID FT_FtAction(');end=text.index('\n}',start)+2;body=text[start:end]
    body=one(body,'\tUINT16 FtActLen;', '\tUINT16 FtActLen,wr_ie_length;')
    anchor='\tos_alloc_mem(pAd, (UCHAR **)&pFtInfo, sizeof(FT_INFO));'
    body=one(body,anchor,''' if(!Elem||!wr_iot_ft_action_payload_length(Elem->MsgLen,sizeof(Elem->Msg),
  LENGTH_802_11,offsetof(FT_ACTION,Oct),&wr_ie_length))return;
'''+anchor)
    check='if(!wr_iot_ft_request_ies_admitted(pFtAction->Oct,wr_ie_length))goto out;\n'
    body=one(body,'pEntry = MacTableLookup(pAd, pHdr->Addr2);',
      check+'\t\t\t\tpEntry = MacTableLookup(pAd, pHdr->Addr2);')
    body=one(body,'if (Elem->Wcid < MAX_LEN_OF_MAC_TABLE)',
      check+'\t\t\t\tif (Elem->Wcid < MAX_LEN_OF_MAC_TABLE)')
    body=one(body,'(FtActLen - sizeof(PFT_ACTION))','wr_ie_length',2)
    # FtActLen remains needed for native forwarding of the complete action.
    text=text[:start]+body+text[end:]
    return text
