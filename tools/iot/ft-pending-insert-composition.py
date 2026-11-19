"""Prepare first-peer FT insertion; never installs or invokes a producer.

Input is an association-generation and peer-owner prepared SDK tree. A private native clone
keeps vendor initialization and existing owner gates. Its ticket claim, peer
absence check, insertion and retirement all execute under the native table lock.
Caller still owns the queued ticket reference and adapter/wdev lifetime.
"""


def one(text, old, new):
    if text.count(old) != 1:
        raise ValueError('FT pending insertion anchor changed: ' + old[:90])
    return text.replace(old, new, 1)


def compose(changes, src, local):
    result = dict(changes)

    def get(name):
        return result[name] if name in result else (src / name).read_text()

    header = get('include/rtmp.h')
    if 'wr_ft_pending_insert' in header:
        raise ValueError('FT pending insertion already prepared')
    for field in ('struct wr_iot_peer_table_owner wr_iot_peer_table_owner;',
                  'struct wr_iot_peer_close_executor wr_iot_peer_close_executor;'):
        if field not in header:
            raise ValueError('FT pending insertion requires peer-owner predecessor: ' + field)
    header = one(header, '\tMAC_TABLE MacTab;',
                 '#ifdef DOT11R_FT_SUPPORT\n'
                 ' struct wr_ft_pending_ledger wr_ft_pending;\n#endif\n\tMAC_TABLE MacTab;')
    # The adapter declaration follows the native MAC table type definitions.
    header = one(header, 'struct _RTMP_ADAPTER {',
                 '#ifdef DOT11R_FT_SUPPORT\n#include "ft-pending-identity.h"\n#endif\n'
                 'struct _RTMP_ADAPTER {')
    prototype = '''#ifdef DOT11R_FT_SUPPORT
struct wr_ft_pending_peer_scope;
MAC_TABLE_ENTRY *wr_ft_pending_insert(RTMP_ADAPTER *pAd,UCHAR *pAddr,
 struct wifi_dev *wdev,const struct wr_ft_pending_token *ticket,
 struct wr_ft_pending_peer_scope *scope);
#endif
'''
    header = one(header, 'MAC_TABLE_ENTRY *MacTableInsertEntry(',
                 prototype + 'MAC_TABLE_ENTRY *MacTableInsertEntry(')
    result['include/rtmp.h'] = header

    init = get('common/rtmp_init.c')
    # Fresh allocation only: do not reset generations on adapter reopen.
    init = one(init, '\t\tpAd->OS_Cookie = handle;' if '\t\tpAd->OS_Cookie = handle;' in init
               else '\t\t\tpAd->OS_Cookie = handle;',
               '#ifdef DOT11R_FT_SUPPORT\n'
               ' wr_ft_pending_ledger_init(&pAd->wr_ft_pending);\n#endif\n'
               '\t\t\tpAd->OS_Cookie = handle;')
    result['common/rtmp_init.c'] = init

    source = get('mgmt/mgmt_entrytb.c')
    source = one(source, '#include <rt_config.h>',
                 '#include <rt_config.h>\n#include "ft-pending-peer-scope.h"')
    signature = ('static MAC_TABLE_ENTRY *wr_iot_mac_insert_entry('
                 if 'static MAC_TABLE_ENTRY *wr_iot_mac_insert_entry(' in source
                 else 'MAC_TABLE_ENTRY *MacTableInsertEntry(')
    start = source.index(signature)
    end = source.index('\n}', start) + 2
    native = source[start:end]
    if 'wr_assoc_publish_slot_locked(pAd,pEntry)' not in native:
        raise ValueError('FT pending insertion requires generation publication')
    native = one(native, '\t\t\tmac_entry_reset(pAd, pEntry, CleanAll);',
        '\t\t\tmac_entry_reset(pAd, pEntry, CleanAll);\n'
        '#ifdef R1KH_HARD_RETRY\n'
        '\t\t\tRTMP_OS_INIT_COMPLETION(&pEntry->ack_r1kh);\n'
        '#endif /* R1KH_HARD_RETRY */')
    clone = one(native, signature, 'static MAC_TABLE_ENTRY *wr_ft_pending_native_insert(')
    at = clone.index(')\n{')
    clone = (clone[:at] + ',\n const struct wr_ft_pending_token *wr_ticket,\n'
        ' struct wr_ft_pending_peer_scope *wr_scope' + clone[at:])
    clone = one(clone, '\tUCHAR HashIdx;', '\tUCHAR HashIdx;\n unsigned int wr_slot; int wr_claimed=0;')
    # Existing table/startup insertion admission remains ahead of this block.
    anchor = '\tfor (i = FirstWcid;'
    pos = clone.index(anchor)
    gate = ''' if(!wr_ticket || !wr_scope || ent_type!=ENTRY_CLIENT || OpMode!=OPMODE_AP ||
  wr_ticket->bss>=pAd->ApCfg.BssidNum ||
  wr_ticket->bss>=sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]) ||
  wr_ticket->bss>=HW_BEACON_MAX_NUM ||
  wdev!=&pAd->ApCfg.MBSSID[wr_ticket->bss].wdev ||
  wdev->func_idx!=wr_ticket->bss || !MAC_ADDR_EQUAL(pAddr,wr_ticket->addr) ||
  !wr_ft_pending_current_locked(&pAd->wr_ft_pending,wr_ticket))goto wr_ft_pending_failure;
 for(wr_slot=1;wr_slot<MAX_LEN_OF_MAC_TABLE;wr_slot++){
  MAC_TABLE_ENTRY *wr_peer=&pAd->MacTab.Content[wr_slot];
  if(!IS_ENTRY_NONE(wr_peer) && MAC_ADDR_EQUAL(wr_peer->Addr,pAddr) &&
   (wr_peer->wdev==wdev || wr_peer->func_tb_idx==wr_ticket->bss))
   goto wr_ft_pending_failure;
 }
 if(!wr_ft_pending_claim_locked(&pAd->wr_ft_pending,wr_ticket))goto wr_ft_pending_failure;
 wr_claimed=1;
'''
    clone = clone[:pos] + gate + clone[pos:]
    clone = one(clone, '\t\t\tmac_entry_reset(pAd, pEntry, CleanAll);',
        '\t\t\tif(!wr_ft_pending_peer_reserve_slot_locked(pAd,i,wdev,wr_ticket,wr_scope)) {\n'
        '\t\t\t\tpEntry=NULL; goto wr_ft_pending_failure;\n'
        '\t\t\t}\n\t\t\tmac_entry_reset(pAd, pEntry, CleanAll);')
    clone = one(clone,
        'if (!wr_assoc_advance_locked(pAd, pEntry, i)) {\n  pEntry = NULL; continue;\n }',
        'if (!wr_assoc_advance_locked(pAd, pEntry, i)) {\n'
        '  (void)wr_ft_pending_peer_cancel_slot_locked(pAd,wr_scope);\n'
        '  pEntry = NULL; continue;\n }')
    # Redirect native post-claim failures to a balanced locked exit. Pre-claim
    # owner admission remains unchanged and may already return without a lock.
    pos = clone.index('\tfor (i = FirstWcid;')
    before, after = clone[:pos], clone[pos:]
    fail = '\t\t\t\t\t\tNdisReleaseSpinLock(&pAd->MacTabLock);\n\t\t\t\t\t\treturn NULL;'
    after = one(after, fail, '\t\t\t\t\t\tgoto wr_ft_pending_failure;')
    after = one(after, '\t\t\t\t\t\treturn NULL;', '\t\t\t\t\t\tgoto wr_ft_pending_failure;')
    clone = before + after
    unlock = 'NdisReleaseSpinLock(&pAd->MacTabLock);'
    pos = clone.rindex(unlock)
    clone = clone[:pos] + '''if(pEntry)(void)wr_ft_pending_peer_publish_locked(pAd,pEntry,wr_ticket,wr_scope);
 if(pEntry)wr_ft_pending_retire_key_locked(&pAd->wr_ft_pending,wr_ticket->bss,pAddr);
 else if(wr_claimed)(void)wr_ft_pending_unclaim_locked(&pAd->wr_ft_pending,wr_ticket);
 ''' + clone[pos:]
    clone = clone[:-2] + '''
wr_ft_pending_failure:
 if(wr_scope&&wr_scope->active&&!wr_scope->generation)
  (void)wr_ft_pending_peer_cancel_slot_locked(pAd,wr_scope);
 if(wr_claimed)(void)wr_ft_pending_unclaim_locked(&pAd->wr_ft_pending,wr_ticket);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return NULL;
}'''
    # Every ordinary successful insertion also invalidates pre-insertion tickets.
    pos = native.rindex(unlock)
    native = native[:pos] + '''
#ifdef DOT11R_FT_SUPPORT
 if(pEntry)wr_ft_pending_retire_key_locked(&pAd->wr_ft_pending,pEntry->func_tb_idx,pEntry->Addr);
#endif
 ''' + native[pos:]
    extra = ',NULL,0' if signature.startswith('static ') else ''
    wrapper = '''
MAC_TABLE_ENTRY *wr_ft_pending_insert(RTMP_ADAPTER *pAd,UCHAR *pAddr,
 struct wifi_dev *wdev,const struct wr_ft_pending_token *ticket,
 struct wr_ft_pending_peer_scope *scope)
{
 MAC_TABLE_ENTRY *result;int entered,ended;
 if(!pAd||!pAddr||!wdev||!ticket||!scope)return NULL;
 NdisZeroMemory(scope,sizeof(*scope));
 NdisAcquireSpinLock(&pAd->MacTabLock);
 entered=wr_iot_peer_close_executor_idle(&pAd->wr_iot_peer_close_executor) &&
  wr_iot_peer_table_transaction_enter(&pAd->wr_iot_peer_table_owner);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(!entered)return NULL;
 result=wr_ft_pending_native_insert(pAd,pAddr,wdev,ENTRY_CLIENT,OPMODE_AP,TRUE''' + extra + ''',ticket,scope);
 NdisAcquireSpinLock(&pAd->MacTabLock);
 ended=wr_iot_peer_table_transaction_leave(&pAd->wr_iot_peer_table_owner);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return ended&&scope->generation?result:NULL;
}
'''
    result['mgmt/mgmt_entrytb.c'] = (source[:start] + native +
        '\n#ifdef DOT11R_FT_SUPPORT\n' + clone + wrapper + '#endif\n' + source[end:])
    result['include/ft-pending-identity.h'] = (local / 'ft-pending-identity.h').read_text()
    return result
