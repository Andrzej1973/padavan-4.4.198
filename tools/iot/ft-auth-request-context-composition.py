"""Thread synchronous FT invocation ownership; prepared only, no installation."""


def one(text, old, new, count=1):
    if text.count(old) != count:
        raise ValueError('FT AUTH request context anchor changed: ' + old[:80])
    return text.replace(old, new)


def compose_callback(text):
    if 'wr_ft_air_request' in text or 'wr_ft_air_scope' not in text:
        raise ValueError('FT AUTH request context requires prepared callback once')
    text = one(text, '#include "ft-auth-peer-scope.h"',
               '#include "ft-auth-peer-scope.h"\n#include "ft-auth-request-context.h"')
    text = one(text, '  int wr_ft_air_failed=0;',
               '  struct wr_ft_auth_request_context wr_ft_air_request={\n'
               '   &wr_ft_air_scope,&wr_ft_air_pending_scope};\n'
               '  int wr_ft_air_failed=0;')
    return one(text, 'FT_AuthReqHandler(pAd, pEntry, &auth_info.FtInfo, pFtInfoBuf)',
               'FT_AuthReqHandler(pAd, pEntry, &auth_info.FtInfo, pFtInfoBuf, &wr_ft_air_request)')


def compose_ft(text, header):
    if 'wr_ft_request_context' in text or 'wr_ft_scope' not in text:
        raise ValueError('FT AUTH request context requires prepared FT consumer once')
    text = one(text, '#include "ft-peer-generation.h"',
               '#include "ft-peer-generation.h"\n#include "ft-auth-request-context.h"')
    # Both the private forward declaration and definition must agree.
    text = one(text, 'OUT PFT_INFO \t\t\tpFtInfo_out)',
               'OUT PFT_INFO \t\t\tpFtInfo_out,\n'
               ' const struct wr_ft_auth_request_context *wr_ft_request_context)', 2)
    signature = 'OUT PFT_INFO pFtInfoBuf)'
    def extend_handler(source):
        start = source.index('USHORT FT_AuthReqHandler(')
        end = source.index(')', start)+1
        declaration = one(source[start:end], signature, signature[:-1] + ',\n'
                          ' const struct wr_ft_auth_request_context *wr_ft_request_context)')
        return source[:start]+declaration+source[end:]
    text = extend_handler(text)
    header = extend_handler(header)
    header = one(header, 'USHORT FT_AuthReqHandler(',
                 'struct wr_ft_auth_request_context;\nUSHORT FT_AuthReqHandler(')
    validation_signature = 'UINT16\tFT_AuthReqRsnValidation('

    def extend_validation(source, expected):
        starts = []
        offset = 0
        while True:
            at = source.find(validation_signature, offset)
            if at < 0:
                break
            starts.append(at)
            offset = at + len(validation_signature)
        if len(starts) != expected:
            raise ValueError('FT AUTH validation declaration count changed')
        for at in reversed(starts):
            close = source.find(')', at)
            if close < 0:
                raise ValueError('FT AUTH validation signature is incomplete')
            source = (source[:close] + ',\n'
                      ' const struct wr_ft_auth_request_context *wr_ft_request_context' +
                      source[close:])
        return source

    text = extend_validation(text, 2)
    text = one(text, ' struct wr_ft_pending_peer_scope wr_ft_pending_scope={0};',
               ' struct wr_ft_pending_peer_scope wr_ft_pending_scope={0};\n'
               ' struct wr_ft_auth_request_context wr_ft_request={\n'
               '  &wr_ft_scope,&wr_ft_pending_scope};')
    text = one(text, 'FT_AuthReqHandler(pAd, pEntry, pFtInfo, pFtInfoBuf)',
               'FT_AuthReqHandler(pAd, pEntry, pFtInfo, pFtInfoBuf, &wr_ft_request)')
    # Avoid reading pEntry until its invocation identity has been checked.
    start = text.index('USHORT FT_AuthReqHandler(')
    end = text.index('\n}', start) + 2
    body = text[start:end]
    body = one(body, 'UCHAR ApIdx = pEntry->func_tb_idx;', 'UCHAR ApIdx;')
    guard = '''
 if(!pAd)return MLME_FAIL_NO_RESOURCE;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if(!wr_ft_auth_request_current_locked(pAd,pEntry,wr_ft_request_context)){
  NdisReleaseSpinLock(&pAd->MacTabLock);return MLME_FAIL_NO_RESOURCE;
 }
 NdisReleaseSpinLock(&pAd->MacTabLock);
'''
    body = one(body, '\tFT_CAP_AND_POLICY FtCapPlc;',
               '\tFT_CAP_AND_POLICY FtCapPlc;\n'+guard+' ApIdx=pEntry->func_tb_idx;')
    body = one(body, 'pFtInfoBuf);',
               'pFtInfoBuf,wr_ft_request_context);')
    text = text[:start]+body+text[end:]
    start = text.index('UINT16\tFT_AuthReqRsnValidation(',
                       text.index('UINT16\tFT_AuthReqRsnValidation(')+1)
    end = text.index('\n}', start)+2
    body = text[start:end]
    body = one(body, '\tULONG temp_len = 0;', '\tULONG temp_len = 0;\n'+guard)
    body = one(body, '\tULONG temp_len = 0;\n'+guard,
               '\tULONG temp_len = 0;\n'+guard+
               ' struct wr_ft_iapp_token_handle wr_ft_local_request={0};\n'
               ' UCHAR wr_ft_wire_token[WR_FT_IAPP_TOKEN_BYTES]={0};\n'
               ' unsigned int wr_ft_response_claimed=0;\n')
    request_zero = 'NdisZeroMemory(&EvtKeyReq, sizeof(FT_KDP_EVT_KEY_ELM));'
    body = one(body, request_zero, request_zero+'''
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if(!wr_ft_local_request.serial &&
    pAd->wr_ft_iapp_requests.current[pEntry->wcid].serial)
  wr_ft_local_request=pAd->wr_ft_iapp_requests.current[pEntry->wcid];
 if(!wr_ft_auth_request_wire_token_locked(pAd,pEntry,wr_ft_request_context,
     &pAd->wr_ft_iapp_requests,&wr_ft_local_request,wr_ft_wire_token,
     &wr_ft_response_claimed)){
  NdisReleaseSpinLock(&pAd->MacTabLock);return MLME_FAIL_NO_RESOURCE;
 }
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(!wr_ft_response_claimed &&
    !wr_ft_iapp_token_pack_reserved(EvtKeyReq.RSV,EvtKeyReq.KeyInfo.RSV,
     wr_ft_wire_token))return MLME_FAIL_NO_RESOURCE;''')
    request_send = '''FT_KDP_EVENT_INFORM(pAd, pEntry->func_tb_idx, FT_KDP_SIG_KEY_REQ_AUTO,
								&EvtKeyReq, sizeof(FT_KDP_EVT_KEY_ELM), NULL);'''
    body = one(body, request_send, 'if(!wr_ft_response_claimed){\n '+request_send+'\n }')
    text=text[:start]+body+text[end:]
    start=text.index('VOID FT_FtAction(');end=text.index('\n}',start)+2
    body=text[start:end]
    body=one(body,'pEntry->Sst = SST_AUTH;', '''NdisAcquireSpinLock(&pAd->MacTabLock);
 if(!wr_ft_auth_request_success_prepare_locked(pAd,pEntry,&wr_ft_request,
     &pAd->wr_ft_iapp_requests)){
  if(!wr_ft_iapp_auth_scope_claimed_locked(pAd,&wr_ft_request,
      &pAd->wr_ft_iapp_requests))
   pAd->wr_iot_peer_table_owner.poisoned=1;
  NdisReleaseSpinLock(&pAd->MacTabLock);goto out;
 }
 pEntry->Sst = SST_AUTH;
 NdisReleaseSpinLock(&pAd->MacTabLock);''')
    text = one(text, '#include "ft-auth-request-context.h"',
               '#include "ft-auth-request-context.h"\n'
               '#include "ft-iapp-auth-owner-transfer.h"')
    cleanup = ''' if(wr_ft_scope.active||wr_ft_pending_scope.active){
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if(wr_ft_scope.active)(void)wr_ft_peer_leave_locked(pAd,&wr_ft_scope);
 if(wr_ft_pending_scope.active)(void)wr_ft_pending_peer_leave_locked(pAd,&wr_ft_pending_scope);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 }'''
    retained = ''' if(wr_ft_scope.active||wr_ft_pending_scope.active){
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if(wr_ft_iapp_auth_scope_claimed_locked(pAd,&wr_ft_request,
     &pAd->wr_ft_iapp_requests)){
  if(!wr_ft_iapp_auth_hold_claimed_locked(pAd,pEntry,&wr_ft_request,
      &pAd->wr_ft_iapp_requests))
   pAd->wr_iot_peer_table_owner.poisoned=1;
 }else{
  if(wr_ft_scope.active)(void)wr_ft_peer_leave_locked(pAd,&wr_ft_scope);
  if(wr_ft_pending_scope.active)(void)wr_ft_pending_peer_leave_locked(pAd,&wr_ft_pending_scope);
 }
 NdisReleaseSpinLock(&pAd->MacTabLock);
 }'''
    retained = retained.replace(''' }else{
  if(wr_ft_scope.active)(void)wr_ft_peer_leave_locked(pAd,&wr_ft_scope);''', ''' }else{
  if(!wr_ft_auth_request_exit_locked(pAd,pEntry,&wr_ft_request,
      &pAd->wr_ft_iapp_requests))
   pAd->wr_iot_peer_table_owner.poisoned=1;
  if(wr_ft_scope.active)(void)wr_ft_peer_leave_locked(pAd,&wr_ft_scope);''')
    body = one(body, cleanup, retained)
    return text[:start]+body+text[end:], header
