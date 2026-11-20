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
    body = one(body, 'pFtInfoBuf);', 'pFtInfoBuf,wr_ft_request_context);')
    text = text[:start]+body+text[end:]
    start = text.index('UINT16\tFT_AuthReqRsnValidation(',
                       text.index('UINT16\tFT_AuthReqRsnValidation(')+1)
    end = text.index('\n}', start)+2
    body = text[start:end]
    body = one(body, '\tULONG temp_len = 0;', '\tULONG temp_len = 0;\n'+guard)
    text=text[:start]+body+text[end:]
    start=text.index('VOID FT_FtAction(');end=text.index('\n}',start)+2
    body=text[start:end]
    body=one(body,'pEntry->Sst = SST_AUTH;', '''NdisAcquireSpinLock(&pAd->MacTabLock);
 if(!wr_ft_auth_request_success_prepare_locked(pAd,pEntry,&wr_ft_request,
     &pAd->wr_ft_iapp_requests)){
  pAd->wr_iot_peer_table_owner.poisoned=1;
  NdisReleaseSpinLock(&pAd->MacTabLock);goto out;
 }
 pEntry->Sst = SST_AUTH;
 NdisReleaseSpinLock(&pAd->MacTabLock);''')
    return text[:start]+body+text[end:], header
