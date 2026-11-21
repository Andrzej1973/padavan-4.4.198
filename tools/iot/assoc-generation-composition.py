"""Compose queued WPA identity generations into the pinned SDK candidate only."""
from pathlib import Path


def one(text, old, new):
    if text.count(old) != 1:
        raise ValueError('association-generation anchor changed: ' + old[:100])
    return text.replace(old, new, 1)


def compose(changes, src, local):
    result = dict(changes)
    def get(name):
        return result.get(name, (src / name).read_text())
    name = 'include/rtmp.h'
    s = get(name)
    if 'unsigned int assoc_gen;' in s:
        raise ValueError('association generation already installed')
    s = one(s, 'typedef struct _MAC_TABLE_ENTRY {',
            'typedef struct _MAC_TABLE_ENTRY {\n unsigned int assoc_gen;')
    # Never put the backing array in MacTab, whose complete clear is native.
    s = one(s, '\tMAC_TABLE MacTab;',
            ' unsigned int wr_assoc_generations[MAX_LEN_OF_MAC_TABLE];\n'
            ' unsigned int wr_assoc_visible[MAX_LEN_OF_MAC_TABLE];\n'
            ' unsigned int wr_assoc_event_users[MAX_LEN_OF_MAC_TABLE];\n'
            ' unsigned int wr_iot_ra2_key_active;\n'
            ' unsigned char wr_assoc_addr[MAX_LEN_OF_MAC_TABLE][6];\n\tMAC_TABLE MacTab;')
    result[name] = s
    name = 'include/mlme.h'
    result[name] = one(get(name), '\tULONG Machine;',
        ' unsigned int assoc_gen;\n'
        ' unsigned short assoc_wcid;\n unsigned char assoc_addr[6];\n\tULONG Machine;')
    # Native full-adapter zero initializes the backing array once. Do not reset
    # it in MacTableReset/ResetWdev or station entry memset.
    name = 'mgmt/mgmt_entrytb.c'
    s = get(name)
    s = one(s, '\t\t\tmac_entry_reset(pAd, pEntry, CleanAll);',
        '\t\t\tmac_entry_reset(pAd, pEntry, CleanAll);\n'
        ' if (!wr_assoc_advance_locked(pAd, pEntry, i)) {\n'
        '  pEntry = NULL; continue;\n }')
    # Delete is already under MacTabLock. Invalidate before teardown side effects.
    s = one(s, '\t\tif (MAC_ADDR_EQUAL(pEntry->Addr, pAddr))\n\t\t{',
        '\t\tif (MAC_ADDR_EQUAL(pEntry->Addr, pAddr))\n\t\t{\n'
        ' (void)wr_assoc_advance_locked(pAd, pEntry, wcid);')
    delete_anchor='\tif (pEntry && !IS_ENTRY_NONE(pEntry))\n\t{'
    s=one(s,delete_anchor,delete_anchor+'\n'
        ' if(pAd->wr_assoc_event_users[wcid]) {\n'
        '  NdisReleaseSpinLock(&pAd->MacTabLock); return FALSE;\n }\n'
        ' if (MAC_ADDR_EQUAL(pEntry->Addr,pAddr)) {\n'
        '  WRITE_ONCE(pAd->wr_assoc_visible[wcid],0); smp_wmb();\n }')
    # Publish once after full insertion/hash initialization, before final unlock.
    # Final peer producer renames the native insertion and replaces the public
    # entry with an include. Publish in the actual private body, never in its
    # counted outer wrapper or in an unrelated declaration.
    signature=('static MAC_TABLE_ENTRY *wr_iot_mac_insert_entry('
        if 'static MAC_TABLE_ENTRY *wr_iot_mac_insert_entry(' in s
        else 'MAC_TABLE_ENTRY *MacTableInsertEntry(')
    if s.count(signature)!=1:
        raise ValueError('native insertion definition changed')
    start=s.index(signature)
    end=s.index('\n}',start)+2
    body=s[start:end]
    if ('mac_entry_reset(pAd, pEntry, CleanAll);' not in body or
        '/* add this MAC entry into HASH table */' not in body):
        raise ValueError('snapshot publication requires native insertion body')
    lock='NdisReleaseSpinLock(&pAd->MacTabLock);'
    at=body.rindex(lock)
    body=body[:at]+'if(pEntry) wr_assoc_publish_slot_locked(pAd,pEntry);\n\t'+body[at:]
    s=s[:start]+body+s[end:]
    result[name] = s
    name = 'ap/ap_repeater.c'
    s = get(name)
    anchor = '\n#ifdef CONFIG_AP_SUPPORT\n#ifdef APCLI_SUPPORT\n\t\tif (apIdx >= MIN_NET_DEVICE_FOR_APCLI)'
    s = one(s, anchor,
        '\n if (!wr_assoc_advance_locked(pAd, pEntry, i)) {\n'
        '  NdisReleaseSpinLock(&pAd->MacTabLock); return NULL;\n }\n' + anchor)
    start=s.index('MAC_TABLE_ENTRY *RTMPInsertRepeaterMacEntry(')
    end=s.index('\n}',start)+2
    body=s[start:end]
    at=body.rindex('NdisReleaseSpinLock(&pAd->MacTabLock);')
    body=body[:at]+'if(pEntry) wr_assoc_publish_slot_locked(pAd,pEntry);\n\t'+body[at:]
    s=s[:start]+body+s[end:]
    result[name] = s
    name = 'ap/ap_assoc.c'
    s = get(name)
    # Both normal association update and the WSC success branch.
    anchor = 'pEntry->Sst = SST_ASSOC;'
    if s.count(anchor) != 2:
        raise ValueError('association success sites changed')
    s = s.replace(anchor,
        'if (!wr_assoc_reassociate(pAd, pEntry))\n'
        ' return MLME_ASSOC_REJ_UNABLE_HANDLE_STA;\n\t' + anchor)
    result[name] = s
    name = 'common/mlme.c'
    s = get(name)
    # Internal MLME + dedicated EAP producers: capture outside queue lock.
    for signature in ('BOOLEAN MlmeEnqueue(', 'BOOLEAN EAPMlmeEnqueue(',
                      'BOOLEAN MlmeEnqueueForRecv('):
        start = s.index(signature)
        end = s.index('\n}', start) + 2
        body = s[start:end]
        body = one(body, '\tINT Tail', '\tstruct wr_assoc_stamp wr_stamp;\n\tINT Tail')
        # Capture immediately before each possible queue lock acquisition.
        for queue in ('Queue', 'EAP_Queue'):
            lock = 'NdisAcquireSpinLock(&(' + queue + '->Lock));'
            if lock in body:
                wc = 'Wcid' if signature == 'BOOLEAN MlmeEnqueueForRecv(' else 'RESERVED_WCID'
                body = one(body, lock,
                    'wr_stamp = wr_assoc_capture(pAd, Machine, MsgLen, Msg, ' + wc + ');\n'
                    ' if (Machine == WPA_STATE_MACHINE && !wr_stamp.gen) return FALSE;\n\t' + lock)
                # Each queue producer publishes a fresh stamp even for non-WPA.
                publish = '\n' + ('\t\t' if signature == 'BOOLEAN MlmeEnqueueForRecv(' else '\t') + queue + '->Entry[Tail].Machine = Machine;'
                body = one(body, publish, publish + '\n'
                    ' wr_assoc_publish(&' + queue + '->Entry[Tail], &wr_stamp);')
        s = s[:start] + body + s[end:]
    # Reject stale WPA before the native delayed/requeue branch as well as dispatch.
    anchor = '\n\t\tif (Elem) \n\t\t{'
    s = one(s, anchor, anchor + '\n'
        ' if (!wr_assoc_event_current(pAd, Elem)) {\n'
        '  wr_assoc_retire_stale_elem(Elem); continue;\n }')
    anchor = 'Queue->Entry[Tail].Machine = Elem->Machine;'
    s = one(s, anchor, anchor + '\n'
        ' Queue->Entry[Tail].assoc_gen = Elem->assoc_gen;\n'
        ' Queue->Entry[Tail].assoc_wcid = Elem->assoc_wcid;\n'
        ' COPY_MAC_ADDR(Queue->Entry[Tail].assoc_addr, Elem->assoc_addr);')
    s = one(s, 'case WPA_STATE_MACHINE:\n\t\t\t\t\tStateMachinePerformAction',
        'case WPA_STATE_MACHINE:\n'
        ' if (!wr_assoc_event_current(pAd, Elem)) break;\n'
        '\t\t\t\t\tStateMachinePerformAction')
    result[name] = s
    name = 'common/cmm_wpa.c'
    s = get(name)
    for signature in ('VOID WpaEAPOLStartAction(', 'VOID WpaEAPOLTimeout(',
                      'VOID WpaEAPOLKeyAction('):
        # Skip a possible forward declaration by requiring the actual body.
        starts = []
        pos = 0
        while True:
            pos = s.find(signature, pos)
            if pos < 0:
                break
            brace = s.find('{', pos)
            semi = s.find(';', pos)
            if brace >= 0 and (semi < 0 or brace < semi):
                starts.append(pos)
            pos += len(signature)
        if len(starts) != 1:
            raise ValueError('WPA action definition changed: ' + signature)
        start = starts[0]
        end = s.index('\n}', start) + 2
        body = s[start:end]
        if signature == 'VOID WpaEAPOLStartAction(':
            body = one(body, '    if (pEntry)\n    {',
                '    if (!wr_assoc_event_entry_current(pAd, Elem, pEntry)) return;\n'
                '    if (pEntry)\n    {')
        elif signature == 'VOID WpaEAPOLTimeout(':
            body = one(body, 'pEntry = MacTableLookup(pAd, Elem->Msg);',
                'pEntry = MacTableLookup(pAd, Elem->Msg);\n'
                ' if (!wr_assoc_event_entry_current(pAd, Elem, pEntry)) return;')
        else:
            body = one(body, '\t\tif (!pEntry || (!IS_ENTRY_CLIENT(pEntry) && !IS_ENTRY_APCLI(pEntry)))',
                ' if (!wr_assoc_event_entry_current(pAd, Elem, pEntry)) break;\n'
                '\t\tif (!pEntry || (!IS_ENTRY_CLIENT(pEntry) && !IS_ENTRY_APCLI(pEntry)))')
            body = one(body, 'WPAInstallSharedKey(pAd, wdev->GroupKeyWepStatus,',
                'if (!wr_assoc_event_entry_current(pAd, Elem, pEntry)) return;\n'
                '\t\t\t\t\t\tWPAInstallSharedKey(pAd, wdev->GroupKeyWepStatus,')
        s = s[:start] + body + s[end:]
    result[name] = s
    for name in ('common/mlme.c', 'mgmt/mgmt_entrytb.c', 'ap/ap_assoc.c', 'ap/ap_repeater.c', 'common/cmm_wpa.c'):
        s = result[name]
        include = '#include <rt_config.h>' if name == 'mgmt/mgmt_entrytb.c' else '#include "rt_config.h"'
        result[name] = one(s, include, include + '\n#include "assoc-generation-kernel.h"')
    for name in ('assoc-generation.h', 'assoc-generation-kernel.h'):
        result['include/' + name] = (local / name).read_text()
    return result
