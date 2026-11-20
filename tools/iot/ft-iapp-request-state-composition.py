"""Prepare adapter-owned FT request registry. Never installs into a build."""


def one(text, old, new):
    if text.count(old) != 1:
        raise ValueError('FT request storage anchor changed: '+old[:80])
    return text.replace(old, new, 1)


def compose(changes, src, local):
    result = dict(changes)
    header = result.get('include/rtmp.h')
    init = result.get('common/rtmp_init.c')
    if header is None or init is None or 'struct wr_ft_pending_ledger wr_ft_pending;' not in header:
        raise ValueError('FT request storage requires pending-identity predecessor')
    if 'wr_ft_iapp_requests' in header or 'wr_ft_iapp_request_state_init' in init:
        raise ValueError('FT request storage already prepared')
    header = one(header, '#include "ft-pending-identity.h"',
                 '#include "ft-pending-identity.h"\n#include "ft-iapp-request-state.h"')
    header = one(header, ' struct wr_ft_pending_ledger wr_ft_pending;',
                 ' struct wr_ft_pending_ledger wr_ft_pending;\n'
                 ' struct wr_ft_iapp_request_state wr_ft_iapp_requests;')
    init = one(init, ' wr_ft_pending_ledger_init(&pAd->wr_ft_pending);',
               ' wr_ft_pending_ledger_init(&pAd->wr_ft_pending);\n'
               ' wr_ft_iapp_request_state_init(&pAd->wr_ft_iapp_requests);')
    result['include/rtmp.h'] = header
    result['common/rtmp_init.c'] = init
    for name in ('ft-iapp-request-state.h', 'ft-iapp-response-token.h'):
        result['include/'+name] = (local/name).read_text()
    return result
