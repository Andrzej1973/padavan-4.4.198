"""Prepare over-air FT AUTH peer lifetime; pipeline installation is prohibited."""


def compose(text):
    if 'wr_ft_air_scope' in text:
        raise ValueError('FT AUTH callback already prepared')
    include='#include "rt_config.h"'
    if text.count(include)!=1:raise ValueError('FT AUTH include anchor changed')
    text=text.replace(include,include+'''
#ifdef DOT11R_FT_SUPPORT
#include "assoc-generation-kernel.h"
#include "ft-auth-peer-scope.h"
#include "ft-pending-peer-scope.h"
MAC_TABLE_ENTRY *wr_ft_pending_insert(RTMP_ADAPTER *,UCHAR *,struct wifi_dev *,
 const struct wr_ft_pending_token *,struct wr_ft_pending_peer_scope *);
#endif
''',1)
    anchor='\tpFtCfg = &pMbss->FtCfg;'
    if text.count(anchor)!=1:raise ValueError('FT AUTH branch anchor changed')
    start=text.index(anchor)
    end=text.index('\n\telse\n#endif /* DOT11R_FT_SUPPORT */',start)
    body=text[start:end]
    declaration='\t\tUSHORT result;'
    if body.count(declaration)!=1:raise ValueError('FT AUTH local anchor changed')
    body=body.replace(declaration,declaration+'''
  struct wr_ft_peer_scope wr_ft_air_scope={0};
  struct wr_ft_pending_peer_scope wr_ft_air_pending_scope={0};
  struct wr_ft_pending_token wr_ft_air_ticket={0};
  int wr_ft_air_failed=0;
''',1)
    old='''\t\tif (!pEntry)
\t\t\tpEntry = MacTableInsertEntry(pAd, auth_info.addr2, wdev, ENTRY_CLIENT, OPMODE_AP, TRUE);'''
    if body.count(old)!=1:raise ValueError('FT AUTH insertion anchor changed')
    body=body.replace(old,'''  NdisAcquireSpinLock(&pAd->MacTabLock);
  if(Elem->assoc_gen){
   if(!wr_ft_auth_existing_enter_locked(pAd,Elem,apidx,auth_info.addr2,
      &wr_ft_air_scope,&pEntry)){
    NdisReleaseSpinLock(&pAd->MacTabLock);return;
   }
   NdisReleaseSpinLock(&pAd->MacTabLock);
  }else{
   pEntry=NULL;
   if(!wr_ft_auth_pending_current_locked(pAd,Elem,apidx,auth_info.addr2,
      &wr_ft_air_ticket)){
    NdisReleaseSpinLock(&pAd->MacTabLock);return;
   }
   NdisReleaseSpinLock(&pAd->MacTabLock);
   pEntry=wr_ft_pending_insert(pAd,auth_info.addr2,wdev,&wr_ft_air_ticket,
     &wr_ft_air_pending_scope);
   if(!pEntry)return;
  }''',1)
    success='pEntry->Sst = SST_AUTH;'
    if body.count(success)!=1:raise ValueError('FT AUTH success anchor changed')
    body=body.replace(success,success+'''
     NdisAcquireSpinLock(&pAd->MacTabLock);
     if((wr_ft_air_scope.active &&
         !wr_ft_peer_advance_locked(pAd,pEntry,&wr_ft_air_scope)) ||
        (wr_ft_air_pending_scope.active &&
         !wr_ft_pending_peer_advance_locked(pAd,pEntry,&wr_ft_air_pending_scope))){
      NdisReleaseSpinLock(&pAd->MacTabLock);
      os_free_mem(NULL,pFtInfoBuf);return;
     }
     NdisReleaseSpinLock(&pAd->MacTabLock);
''',1)
    failure='goto auth_failure;'
    if body.count(failure)!=1:raise ValueError('FT AUTH failure anchor changed')
    body=body.replace(failure,'goto wr_ft_air_failure;',1)
    final='\t\treturn;\n\t}'
    if not body.endswith(final):raise ValueError('FT AUTH final return anchor changed')
    body=body[:-len(final)]+'''  goto wr_ft_air_done;
wr_ft_air_failure:
  wr_ft_air_failed=1;
wr_ft_air_done:
  NdisAcquireSpinLock(&pAd->MacTabLock);
  if(wr_ft_air_scope.active)(void)wr_ft_peer_leave_locked(pAd,&wr_ft_air_scope);
  if(wr_ft_air_pending_scope.active)
   (void)wr_ft_pending_peer_leave_locked(pAd,&wr_ft_air_pending_scope);
  NdisReleaseSpinLock(&pAd->MacTabLock);
  if(wr_ft_air_failed)goto auth_failure;
  return;
 }'''
    return text[:start]+body+text[end:]
