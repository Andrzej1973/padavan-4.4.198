"""Prepare outer native association/auth wrappers; not installed by CI producer.

The Linux admission binding must provide wr_ra2_mutation_enter/leave before
this can be included in a buildable candidate. Refuse source/signature drift.
"""
import re

SITES = {
    'ap/ap_assoc.c': [('ap_cmm_peer_assoc_req_action', False, True)],
    'ap/ap_auth.c': [('APPeerAuthReqAtIdleAction', True, False),
                     ('APPeerAuthConfirmAction', True, False)],
}
GUARD = '#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'


def compose(name, source):
    receipts = []
    for function, static, reassoc in SITES[name]:
        raw = 'wr_ra2_native_' + function
        if raw in source:
            raise ValueError('mutation wrapper already present: ' + function)
        pattern = (r'(?m)^' + ('static ' if static else '') + r'VOID\s+' +
                   function + r'\(\s*(?:IN\s+)?(?:PRTMP_ADAPTER|RTMP_ADAPTER\s*\*)\s*pAd,\s*'
                   r'(?:IN\s+)?MLME_QUEUE_ELEM\s*\*\s*Elem' +
                   (r',\s*IN\s+BOOLEAN\s+isReassoc' if reassoc else '') + r'\)\s*(?=\{)')
        matches = list(re.finditer(pattern, source))
        if len(matches) != 1:
            raise ValueError('native mutation definition changed: ' + function)
        match = matches[0]
        arguments = 'RTMP_ADAPTER *pAd,MLME_QUEUE_ELEM *Elem'
        call = 'pAd,Elem'
        if reassoc:
            arguments += ',BOOLEAN isReassoc'
            call += ',isReassoc'
        wrapper = ('static VOID ' + raw + '(' + arguments + ');\n' +
                   ('static ' if static else '') + 'VOID ' + function + '(' + arguments + ')\n{\n' +
                   GUARD + '\n struct wr_ra2_assoc_ticket ticket={0};\n'
                   ' int admitted=wr_ra2_mutation_enter(pAd,Elem,&ticket);\n'
                   ' if(admitted<0)return;\n' +
                   ' ' + raw + '(' + call + ');\n'
                   ' if(admitted>0)wr_ra2_mutation_leave(pAd,&ticket);\n'
                   '#else\n ' + raw + '(' + call + ');\n#endif\n}\n' +
                   'static VOID ' + raw + '(' + arguments + ')\n')
        old = source[match.start():match.end()]
        source = source[:match.start()] + wrapper + source[match.end():]
        receipts.append((wrapper, old))
    return source, receipts
