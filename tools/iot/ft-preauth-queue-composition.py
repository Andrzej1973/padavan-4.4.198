"""Prepare native MLME retry sidecar lifecycle; never install into a build."""


def one(text, old, new):
    if text.count(old) != 1:
        raise ValueError('FT preauth queue anchor changed: '+old[:90])
    return text.replace(old, new, 1)


def compose(changes, src, local):
    result = dict(changes)
    header = result.get('include/mlme.h', '')
    mlme = result.get('common/mlme.c', '')
    kernel = result.get('include/assoc-generation-kernel.h', '')
    if 'ft_preauth_serial' in header:
        raise ValueError('FT preauth queue already prepared')
    if 'unsigned int assoc_gen;' not in header or 'wr_assoc_publish(' not in mlme:
        raise ValueError('FT preauth queue requires generation predecessor')
    fields = '''#ifdef DOT11R_FT_SUPPORT
 unsigned int ft_preauth_serial,ft_preauth_generation,ft_preauth_wcid,ft_preauth_bss;
 unsigned char ft_preauth_mac[6],ft_preauth_bssid[6];
#endif
'''
    header = one(header, ' unsigned int assoc_gen;', fields+' unsigned int assoc_gen;')
    # Every producer and generated clone already uses wr_assoc_publish. Clear
    # sidecar here before a specialized retry producer publishes its own stamp.
    anchor = ' elem->assoc_gen = stamp->gen;'
    kernel = one(kernel, anchor, '#ifdef DOT11R_FT_SUPPORT\n'
                 ' wr_ft_preauth_elem_clear(elem);\n#endif\n'+anchor)
    kernel = '#ifdef DOT11R_FT_SUPPORT\n#include "ft-preauth-queue.h"\n#endif\n'+kernel
    start = mlme.index('NDIS_STATUS MlmeQueueInit(')
    end = mlme.index('\n}', start)+2
    body = mlme[start:end]
    for queue in ('Queue', 'EAP_Queue'):
        marker = '\t\t'+queue+'->Entry[i].Occupied = FALSE;'
        if marker in body:
            body = one(body, marker, '#ifdef DOT11R_FT_SUPPORT\n'
                       ' wr_ft_preauth_elem_clear(&'+queue+'->Entry[i]);\n#endif\n'+marker)
    mlme = mlme[:start]+body+mlme[end:]
    anchor = 'Queue->Entry[Tail].assoc_gen = Elem->assoc_gen;'
    copy = '''
#ifdef DOT11R_FT_SUPPORT
 Queue->Entry[Tail].ft_preauth_serial=Elem->ft_preauth_serial;
 Queue->Entry[Tail].ft_preauth_generation=Elem->ft_preauth_generation;
 Queue->Entry[Tail].ft_preauth_wcid=Elem->ft_preauth_wcid;
 Queue->Entry[Tail].ft_preauth_bss=Elem->ft_preauth_bss;
 COPY_MAC_ADDR(Queue->Entry[Tail].ft_preauth_mac,Elem->ft_preauth_mac);
 COPY_MAC_ADDR(Queue->Entry[Tail].ft_preauth_bssid,Elem->ft_preauth_bssid);
#endif
'''
    mlme = one(mlme, anchor, anchor+copy)
    result['include/mlme.h'] = header
    result['common/mlme.c'] = mlme
    result['include/assoc-generation-kernel.h'] = kernel
    for name in ('ft-preauth-queue.h', 'ft-iapp-request-state.h', 'ft-iapp-response-token.h'):
        result['include/'+name] = (local/name).read_text()
    return result
