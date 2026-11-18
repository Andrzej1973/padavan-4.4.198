"""Compose native ra2 mutation wrappers plus their Linux admission implementation.

Preparation only: not called by the candidate installer until insertion and
both key-writer bindings participate in the same arbitration protocol.
"""
import runpy


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('mutation binding anchor changed: ' + old)
    return text.replace(old, new, 1)


def compose(changes, src, local):
    result = dict(changes)
    def get(name):
        return result.get(name, (src/name).read_text())
    header = get('include/rtmp.h')
    if 'struct wr_ra2_assoc_owner wr_ra2_assoc_owner;' in header:
        raise ValueError('mutation binding already installed')
    header = replace_once(header, 'typedef struct _MAC_TABLE_ENTRY {',
        '#include "ra2-association-owner.h"\ntypedef struct _MAC_TABLE_ENTRY {')
    header = replace_once(header, ' unsigned int wr_iot_ra2_key_active;',
        ' unsigned int wr_iot_ra2_key_active;\n struct wr_ra2_assoc_owner wr_ra2_assoc_owner;')
    result['include/rtmp.h'] = header
    module = runpy.run_path(str(local/'ra2-mutation-wrappers.py'))
    for name in module['SITES']:
        text, _ = module['compose'](name, get(name))
        text = replace_once(text, '#include "rt_config.h"',
            '#include "rt_config.h"\n'+module['GUARD']+
            '\n#include "ra2-mutation-admission-kernel.h"\n#endif')
        result[name] = text
    for name in ('ra2-association-owner.h', 'ra2-mutation-admission-kernel.h'):
        result['include/'+name] = (local/name).read_text()
    return result


def compose_insertion(text):
    """Wrap the entire existing public insertion fragment, preserving its body."""
    signature='MAC_TABLE_ENTRY *MacTableInsertEntry('
    if 'wr_ra2_native_public_insert' in text:
        raise ValueError('insertion mutation wrapper already present')
    if text.count(signature)!=1 or text.count('wr_iot_peer_table_transaction_enter(')!=1:
        raise ValueError('public insertion transaction fragment changed')
    raw=text.replace(signature,'static MAC_TABLE_ENTRY *wr_ra2_native_public_insert(',1)
    return raw+'''
MAC_TABLE_ENTRY *MacTableInsertEntry(RTMP_ADAPTER *pAd,UCHAR *pAddr,
 struct wifi_dev *wdev,UINT32 ent_type,UCHAR OpMode,BOOLEAN CleanAll)
{
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 struct wr_ra2_assoc_ticket ticket={0};
 MAC_TABLE_ENTRY *result;
 int admitted=wr_ra2_mutation_enter_wdev(pAd,wdev,&ticket);
 if(admitted<0)return NULL;
 result=wr_ra2_native_public_insert(pAd,pAddr,wdev,ent_type,OpMode,CleanAll);
 if(admitted>0)wr_ra2_mutation_leave(pAd,&ticket);
 return result;
#else
 return wr_ra2_native_public_insert(pAd,pAddr,wdev,ent_type,OpMode,CleanAll);
#endif
}
'''


def compose_all(changes, src, local):
    """Compose a complete arbitration preview, retaining peer-lifetime gate.

    Inputs are the already prepared Linux API tree. No pristine fallback for
    the public insertion fragment: it must exist in the reviewed predecessor.
    """
    result=compose(changes,src,local)
    insertion='include/wr-iot-peer-normal-insert.inc'
    result[insertion]=compose_insertion(result[insertion] if insertion in result else (src/insertion).read_text())
    # The public fragment is included by mgmt_entrytb after rt_config.h.
    name='mgmt/mgmt_entrytb.c'
    text=result[name] if name in result else (src/name).read_text()
    guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
    text=replace_once(text,'#include <rt_config.h>',
        '#include <rt_config.h>\n'+guard+'\n#include "ra2-mutation-admission-kernel.h"\n#endif')
    result[name]=text
    key=runpy.run_path(str(local/'ra2-key-arbitration-composition.py'))
    name='include/ra2-gtk-request-kernel.h'
    result[name]=key['request_header'](result[name] if name in result else (src/name).read_text())
    name='ap/ap_wpa.c'
    result[name]=key['periodic'](result[name] if name in result else (src/name).read_text())
    result[name]=key['periodic_peer_scope'](result[name])
    result['include/ra2-rekey-peer-scope.h']=(local/'ra2-rekey-peer-scope.h').read_text()
    return result
