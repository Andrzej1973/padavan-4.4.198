#!/usr/bin/env python3
"""Check bounded FT parsing is scoped to terminating request/confirm branches."""
import argparse,runpy
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
native=(a.source/'common/ft.c').read_text()
compose=runpy.run_path(str(here/'ft-parser-bounds-composition.py'))['compose']
text=compose(native);start=text.index('VOID FT_FtAction(');body=text[start:text.index('\n}',start)+2]
check='if(!wr_iot_ft_request_ies_admitted(pFtAction->Oct,wr_ie_length))goto out;'
assert body.count(check)==2
assert body.index('wr_iot_ft_action_payload_length')<body.index('os_alloc_mem')
assert 'wr_iot_ft_request_ies_admitted' not in body[:body.index('switch(pFtAction->Action)')]
request=body[body.index('case FT_ACTION_BT_REQ:'):body.index('case FT_ACTION_BT_CONFIRM:')]
assert request.index(check)<request.index('MacTableLookup')<request.index('FT_AuthReqHandler')
confirm=body[body.index('case FT_ACTION_BT_CONFIRM:'):]
assert confirm.index(check)<confirm.index('if (Elem->Wcid < MAX_LEN_OF_MAC_TABLE)')<confirm.index('FT_AuthConfirmHandler')
# Both forwarding call sites remain byte-identical; they are outside the
# terminating branches guarded above. No generic TLV check before the switch.
for fragment in (
 'FT_RrbEnqueue(pAd, pFtAction->TargetApAddr,\n\t\t\t\t\t\t\t(PFT_ACTION)pFtAction, FtActLen, apidx);',):
 assert native.count(fragment)==text.count(fragment)>0
assert 'sizeof(PFT_ACTION)' not in body
assert request.index('if(!pEntry)goto out;')>request.index('MacTableInsertEntry')
assert request.index('if(!pEntry)goto out;')<request.index('FT_ReqActionParse')
assert 'if (pEntry->func_tb_idx >= pAd->ApCfg.BssidNum)' in confirm
assert 'if (pEntry->func_tb_idx > pAd->ApCfg.BssidNum)' not in confirm
try:compose(text)
except ValueError:pass
else:raise AssertionError('duplicate accepted')
print('FT bounds composition: outer admission, terminating request/confirm validation before lookup, native forwarding preserved PASS')
