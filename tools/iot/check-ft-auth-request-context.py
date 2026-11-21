#!/usr/bin/env python3
"""Check pinned FT ownership argument threading; execute AUTH callback fixture."""
import argparse
import ast
import contextlib
import io
import re
import runpy
import subprocess
import sys
import tempfile
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
a = p.parse_args()
here = Path(__file__).resolve().parent
native = (a.source/'common/ft.c').read_text()
header = (a.source/'include/ft.h').read_text()
schema = runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']({}, a.source, here)
enqueue = runpy.run_path(str(here/'ft-enqueue-generation-composition.py'))
mlme, proto = enqueue['compose'](schema['common/mlme.c'])
pending_enqueue = runpy.run_path(str(here/'ft-pending-enqueue-composition.py'))
mlme, pending_proto = pending_enqueue['compose'](mlme)
ordinary_rx = runpy.run_path(str(here/'ft-rx-generation-composition.py'))['compose'](
    mlme, proto, pending_proto)
bounded = runpy.run_path(str(here/'ft-parser-bounds-composition.py'))['compose'](native)
prepared = enqueue['bind_ft'](bounded, proto, pending_proto)
module = runpy.run_path(str(here/'ft-auth-request-context-composition.py'))
composed, composed_header = module['compose_ft'](prepared, header)
# Exercise the next real target-composition consumer: an include inserted before
# a saved body offset must not splice FT_FtAction into its preceding comment.
wrapped, wrapper_receipts = runpy.run_path(
    str(here/'ra2-ft-mutation-composition.py'))['compose'](composed)
assert len(wrapper_receipts) == 1
wrapper, original_definition = wrapper_receipts[0]
assert wrapped.replace(wrapper, original_definition, 1) == composed
assert '\nVOID FT_FtAction(' in composed
# Both native validation declarations receive exactly one context parameter.
validation_signatures = re.findall(r'UINT16\s+FT_AuthReqRsnValidation\([^)]*\)', composed)
assert len(validation_signatures) == 2
for signature in validation_signatures:
    assert signature.count('wr_ft_request_context') == 1
validation_start = composed.rindex('UINT16\tFT_AuthReqRsnValidation(')
validation_body = composed[validation_start:composed.index('\n}', validation_start)]
assert validation_body.index('unsigned int wr_ft_response_claimed=0;') < validation_body.index('if(!pAd)')
# Validate the target probe's exact copied local-header closure, including
# nested includes. Vendor headers continue to resolve through native Kbuild.
probe_tree = ast.parse((here/'check-ft-bounds-target-tu.py').read_text())
symbol_loops = [node for node in ast.walk(probe_tree)
                if isinstance(node, ast.For) and isinstance(node.iter, ast.Tuple)
                and any(isinstance(item, ast.Constant)
                        and item.value == 'wr_ft_mlme_enqueue_for_recv'
                        for item in node.iter.elts)]
assert len(symbol_loops) == 2
for loop in symbol_loops:
    assert any(isinstance(item, ast.Constant) and item.value == 'FT_AuthReqHandler'
               for item in loop.iter.elts), 'AUTH contract symbol omitted from target inventory'
header_sets = [
    {element.value for element in node.iter.elts}
    for node in ast.walk(probe_tree)
    if isinstance(node, ast.For) and isinstance(node.iter, ast.Tuple)
    and all(isinstance(element, ast.Constant) and isinstance(element.value, str)
            for element in node.iter.elts)
    and any(isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == 'shutil' and call.func.attr == 'copyfile'
            for call in ast.walk(node))]
assert len(header_sets) == 1
# Execute the target probe's real source selector without its CLI/build body.
selector_node = next(node for node in probe_tree.body
                     if isinstance(node, ast.FunctionDef)
                     and node.name == 'probe_header_source')
selector_scope = {}
exec(compile(ast.Module(body=[selector_node], type_ignores=[]),
             'probe-header-selector', 'exec'), selector_scope)
select_header = selector_scope['probe_header_source']
with tempfile.TemporaryDirectory(prefix='ft-probe-header-source-') as td:
    driver = Path(td)/'driver'
    (driver/'include').mkdir(parents=True)
    live = driver/'include/radio-transition.h'
    live.write_bytes((here/'radio-transition-api.h').read_bytes())
    chosen = select_header(here, driver, live.name)
    assert chosen == live and chosen.read_bytes() == live.read_bytes()
    assert chosen.read_bytes() != (here/live.name).read_bytes()
    probe = Path(td)/'probe.c'
    probe.write_text('#include "radio-transition.h"\nint probe(void){return WR_RADIO_BSS_OBSERVE;}\n')
    command = ['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-fsyntax-only']
    subprocess.run([*command, '-I'+str(chosen.parent), str(probe)], check=True)
    frozen = subprocess.run([*command, '-I'+str(here), str(probe)],
                            capture_output=True, text=True)
    assert frozen.returncode != 0 and 'WR_RADIO_BSS_OBSERVE' in frozen.stderr
    assert select_header(here, driver, 'ft-auth-request-context.h') == here/'ft-auth-request-context.h'
    try:
        select_header(here, driver, 'radio-transition-api.h')
    except ValueError:
        pass
    else:
        raise AssertionError('missing prepared header silently replaced by frozen base')
probe_headers = header_sets[0]
for text in [composed, composed_header, *[(here/name).read_text()
                                        for name in sorted(probe_headers)]]:
    for name in re.findall(r'^\s*#include\s+"([^"\n]+)"', text, re.M):
        if (here/name).is_file():
            assert name in probe_headers, 'target probe missing local header: '+name
storage_input = dict(schema)
storage_input['include/rtmp.h'] = storage_input['include/rtmp.h'].replace(
    '\tMAC_TABLE MacTab;',
    ' struct wr_iot_peer_table_owner wr_iot_peer_table_owner;\n'
    ' struct wr_iot_peer_close_executor wr_iot_peer_close_executor;\n\tMAC_TABLE MacTab;', 1)
storage_input = runpy.run_path(str(here/'ft-pending-insert-composition.py'))['compose'](
    storage_input, a.source, here)
storage_compose = runpy.run_path(str(here/'ft-iapp-request-state-composition.py'))['compose']
storage = storage_compose(storage_input, a.source, here)
delete_compose=runpy.run_path(str(here/'ft-iapp-delete-composition.py'))['compose']
delete_prepared=delete_compose(storage,a.source,here)
delete_source=delete_prepared['mgmt/mgmt_entrytb.c']
gate=delete_source.index('if(!wr_ft_iapp_slot_retire_locked(')
assert gate<delete_source.index('WRITE_ONCE(pAd->wr_assoc_visible[wcid],0);',gate)
assert gate<delete_source.index('(void)wr_assoc_advance_locked(pAd, pEntry, wcid);',gate)
for invalid in ({},delete_prepared):
    try:delete_compose(invalid,a.source,here)
    except ValueError:pass
    else:raise AssertionError('missing delete predecessor or duplicate accepted')
init = storage['common/rtmp_init.c']
init_call = ' wr_ft_iapp_request_state_init(&pAd->wr_ft_iapp_requests);'
assert init.count(init_call) == 1
alloc_start = init.index('NDIS_STATUS RTMPAllocAdapterBlock(')
alloc_end = init.index('\n}', alloc_start)
assert alloc_start < init.index(init_call) < init.index('pAd->OS_Cookie = handle;', alloc_start) < alloc_end
assert init.count('get_random_bytes(wr_ft_seed,sizeof(wr_ft_seed));') == 1
assert init.index(init_call) < init.index('get_random_bytes(wr_ft_seed,') < init.index('wr_ft_iapp_request_state_seed(') < alloc_end
assert storage['include/rtmp.h'].count('struct wr_ft_iapp_request_state wr_ft_iapp_requests;') == 1
assert storage['include/ft-iapp-request-state.h'] == (here/'ft-iapp-request-state.h').read_text()
for invalid in ({}, storage):
    try:
        storage_compose(invalid, a.source, here)
    except ValueError:
        pass
    else:
        raise AssertionError('missing storage predecessor or duplicate accepted')


def signatures(text, name):
    return [re.sub(r'\s+', '', value) for value in re.findall(
        r'(?:USHORT|UINT16)\s+'+name+r'\([^)]*\)', text)]


assert signatures(composed, 'FT_AuthReqHandler') == signatures(composed_header, 'FT_AuthReqHandler')
validation = signatures(composed, 'FT_AuthReqRsnValidation')
assert len(validation) == 2 and validation[0] == validation[1]
assert validation[0].endswith(
    'conststructwr_ft_auth_request_context*wr_ft_request_context)')
assert composed.count('pFtInfoBuf,wr_ft_request_context);') == 1
assert composed.count('pFtInfoBuf, &wr_ft_request)') == 1
action_start=composed.index('VOID FT_FtAction(')
action=composed[action_start:composed.index('\n}',action_start)+2]
assert action.index('wr_ft_auth_request_success_prepare_locked(')<action.index('pEntry->Sst = SST_AUTH;')<action.index('wr_ft_pending_peer_advance_locked(')
# Check the producer/consumer provenance as one composed source contract:
# ordinary RX captures the same BSS+MAC identity that FT_FtAction later claims.
assert ordinary_rx.count('wr_ft_rx_pending') >= 3
assert 'wr_ft_peer_capture_locked(pAd,wr_wcid,wr_apidx,wr_frame->Hdr.Addr2,&wr_stamp)' in ordinary_rx
assert 'wr_ft_pending_reserve_locked(&pAd->wr_ft_pending,wr_apidx' in ordinary_rx
assert 'return FALSE;\n }\n#endif\n return wr_ft_native_mlme_enqueue_for_recv' in ordinary_rx
assert action.index('if(Elem->assoc_gen)') < action.index('wr_ft_peer_enter_locked(') < action.index('FT_AuthReqHandler(')
assert 'Elem->Wcid!=Elem->assoc_wcid' in action
assert 'wr_ft_expected.bss=apidx' in action
request=action[action.index('case FT_ACTION_BT_REQ:'):action.index('case FT_ACTION_BT_CONFIRM:')]
assert request.index('wr_ft_ticket.bss!=apidx') < request.index('wr_ft_pending_current_locked(')
assert request.index('wr_ft_pending_current_locked(') < request.index('wr_ft_pending_insert(') < request.index('FT_AuthReqHandler(')
assert 'MacTableLookup' not in request and 'MacTableInsertEntry' not in request
assert action.index('wr_ft_pending_peer_advance_locked(') < action.index('FT_RrbEnqueue(')
for name in ('USHORT FT_AuthReqHandler(', 'UINT16\tFT_AuthReqRsnValidation('):
    start = composed.rindex(name)
    body = composed[start:composed.index('\n}', start)+2]
    assert body.index('wr_ft_auth_request_current_locked(') < body.index('pEntry->')
    assert body.index('NdisAcquireSpinLock(') < body.index('wr_ft_auth_request_current_locked(')
    assert body.count('NdisAcquireSpinLock(') >= 1
    assert body.count('NdisReleaseSpinLock(') >= 1
    if name.startswith('UINT16'):
        assert 'wr_ft_auth_request_wire_token_locked(' in body
        assert 'wr_ft_iapp_token_pack_reserved(EvtKeyReq.RSV,EvtKeyReq.KeyInfo.RSV,' in body
        assert body.index('wr_ft_iapp_token_pack_reserved(') < body.index('FT_KDP_EVENT_INFORM(pAd, pEntry->func_tb_idx')
for invalid in (native, composed):
    try:
        module['compose_ft'](invalid, header)
    except ValueError:
        pass
    else:
        raise AssertionError('missing predecessor or duplicate accepted')
drift = prepared.replace('pFtInfoBuf);', 'pFtInfoBuf /* drift */);', 1)
try:
    module['compose_ft'](drift, header)
except ValueError:
    pass
else:
    raise AssertionError('validation call drift accepted')
argv = sys.argv[:]
sys.argv = [str(here/'check-ft-auth-callback.py'), str(a.source), '--request-context']
try:
    with contextlib.redirect_stdout(io.StringIO()) as output:
        fixture = runpy.run_path(sys.argv[0])
finally:
    sys.argv = argv
print(output.getvalue(), end='')
# Execute the entire generated native handler too. RSN cryptography remains
# an explicit actor; callback, handler, identity checks and exits are real.
prefix = fixture['prefix'].replace(
    'typedef struct {unsigned char value[8];} FT_MDIE_INFO;', '''
typedef union {struct {unsigned FtOverDs:1,RsrReqCap:1;} field;unsigned word;} FT_CAP_AND_POLICY;
typedef struct {unsigned char Len,MdId[2];FT_CAP_AND_POLICY FtCapPlc;} FT_MDIE_INFO;
''').replace('struct {int Dot11rFtEnable;} FtCapFlag;',
             'unsigned char FtMdId[2];struct {int Dot11rFtEnable,FtOverDs,RsrReqCap;} FtCapFlag;')
prefix += '''
typedef RTMP_ADAPTER *PRTMP_ADAPTER;
typedef FT_INFO *PFT_INFO;
#ifndef DBGPRINT
#define DBGPRINT(a,b) ((void)0)
#endif
#ifndef DBGPRINT_ERR
#define DBGPRINT_ERR(a) ((void)0)
#endif
#define OUT
#define FT_MDID_EQU(a,b) (!memcmp(a,b,2))
#define FT_SET_MDID(a,b) memcpy(a,b,2)
#define MLME_UNSPECIFY_FAIL 56
#define FT_STATUS_CODE_INVALID_MDIE 54
#ifndef NdisZeroMemory
#define NdisZeroMemory(a,n) memset(a,0,n)
#endif
'''
start = composed.index('USHORT FT_AuthReqHandler(')
handler = composed[start:composed.index('\n}', start)+2]
actors = fixture['actors']
start = actors.index('static USHORT FT_AuthReqHandler(')
end = actors.index('\n}', start)+2
validation_actor = r'''
static USHORT FT_AuthReqRsnValidation(PRTMP_ADAPTER ad,PMAC_TABLE_ENTRY entry,
 PFT_CFG cfg,PFT_INFO in,PFT_INFO out,
 const struct wr_ft_auth_request_context *context){
 struct wr_ft_iapp_token_ledger ledger;
 struct wr_ft_iapp_token_handle request={0},response={0},saved;
 unsigned char token[7]={1,2,3,4,5,6,7},wrong[7]={9};
 (void)cfg;(void)in;(void)out;
 NdisAcquireSpinLock(&ad->MacTabLock);
 assert(wr_ft_auth_request_current_locked(ad,entry,context));
 wr_ft_iapp_token_ledger_init(&ledger);
 assert(wr_ft_auth_request_begin_locked(ad,entry,context,&ledger,token,&request));
 saved=request;
 assert(!wr_ft_auth_request_begin_locked(ad,entry,context,&ledger,wrong,&request));
 assert(request.serial==saved.serial&&request.slot==saved.slot);
 assert(!wr_ft_auth_request_admit_locked(ad,entry,context,&ledger,wrong,
  entry->Addr,entry->wdev->bssid,&request,&response));
 assert(!response.serial);
 assert(!wr_ft_auth_request_admit_locked(ad,entry,NULL,&ledger,token,
  entry->Addr,entry->wdev->bssid,&request,&response));
 assert(!wr_ft_auth_request_admit_locked(ad,entry,context,&ledger,token,
  entry->Addr,entry->wdev->bssid,&request,&request));
 assert(request.serial==saved.serial);
 assert(wr_ft_auth_request_admit_locked(ad,entry,context,&ledger,token,
  entry->Addr,entry->wdev->bssid,&request,&response));
 assert(!wr_ft_auth_request_end_locked(ad,entry,context,&ledger,&request));
 assert(request.serial==saved.serial&&ad->wr_assoc_event_users[entry->wcid]==1);
 assert(wr_ft_iapp_token_finish_locked(&ledger,&response));
 assert(wr_ft_auth_request_end_locked(ad,entry,context,&ledger,&request));
 assert(!request.serial);
 token[0]++;
 assert(wr_ft_auth_request_begin_locked(ad,entry,context,&ledger,token,&request));
 assert(wr_ft_auth_request_end_locked(ad,entry,context,&ledger,&request));
 assert(!wr_ft_auth_request_admit_locked(ad,entry,context,&ledger,token,
  entry->Addr,entry->wdev->bssid,&request,&response));
 assert(!response.serial&&ad->wr_assoc_event_users[entry->wcid]==1);
 {
 struct wr_ft_iapp_request_state state;
 struct wr_ft_iapp_token_handle active={0},old={0},other={0},claim={0};
 unsigned int serial;
 memset(&state,0xa5,sizeof(state));wr_ft_iapp_request_state_init(&state);
 assert(!state.ledger.next_serial&&!state.ledger.poisoned);
 for(unsigned int w=0;w<WR_FT_IAPP_TOKEN_CAPACITY;w++)assert(!state.request_by_wcid[w].serial);
 assert(!wr_ft_auth_request_publish_locked(ad,entry,context,&state,token,&state.request_by_wcid[1]));
 assert(!state.ledger.next_serial&&!state.request_by_wcid[1].serial);
 assert(wr_ft_auth_request_publish_locked(ad,entry,context,&state,token,&active));
 old=active;serial=state.ledger.next_serial;
 assert(!wr_ft_auth_request_unpublish_locked(ad,entry,context,&state,&state.request_by_wcid[1]));
 assert(!wr_ft_auth_request_publish_locked(ad,entry,context,&state,wrong,&other));
 assert(!other.serial&&state.ledger.next_serial==serial);
 assert(!wr_ft_auth_request_publish_locked(ad,entry,context,&state,wrong,&state.request_by_wcid[entry->wcid]));
 assert(state.request_by_wcid[entry->wcid].serial==active.serial);
 assert(wr_ft_auth_request_admit_locked(ad,entry,context,&state.ledger,token,
  entry->Addr,entry->wdev->bssid,&state.request_by_wcid[entry->wcid],&claim));
 assert(!wr_ft_auth_request_unpublish_locked(ad,entry,context,&state,&active));
 assert(!wr_ft_auth_request_success_prepare_locked(ad,entry,context,&state));
 assert(active.serial&&state.request_by_wcid[entry->wcid].serial==active.serial);
 assert(wr_ft_iapp_token_finish_locked(&state.ledger,&claim));
 assert(wr_ft_auth_request_unpublish_locked(ad,entry,context,&state,&active));
 assert(!active.serial&&!state.request_by_wcid[entry->wcid].serial);
 token[0]++;
 assert(wr_ft_auth_request_publish_locked(ad,entry,context,&state,token,&active));
 assert(active.serial>old.serial&&state.ledger.next_serial>serial);
 assert(!wr_ft_auth_request_unpublish_locked(ad,entry,context,&state,&old));
 assert(state.request_by_wcid[entry->wcid].serial==active.serial);
 assert(wr_ft_auth_request_unpublish_locked(ad,entry,context,&state,&active));
 assert(state.ledger.next_serial>serial);
 {
 unsigned char seed[7]={0},wire[7],first_wire[7];unsigned int response_claimed;
 assert(wr_ft_iapp_request_state_seed(&state,seed));
 assert(wr_ft_auth_request_publish_next_locked(ad,entry,context,&state,&active,wire));
 assert(wr_ft_iapp_token_nonzero(wire));memcpy(first_wire,wire,7);
 assert(wr_ft_iapp_token_equal(state.ledger.entry[active.slot].token,wire));
 assert(wr_ft_auth_request_wire_token_locked(ad,entry,context,&state,&active,
  wire,&response_claimed));
 assert(!response_claimed&&wr_ft_iapp_token_equal(first_wire,wire));
 entry->assoc_gen++;
 assert(!wr_ft_auth_request_wire_token_locked(ad,entry,context,&state,&active,
  wire,&response_claimed));
 assert(!wr_ft_iapp_token_nonzero(wire));
 entry->assoc_gen--;
 assert(!wr_ft_auth_request_publish_next_locked(ad,entry,context,&state,&other,wire));
 assert(!wr_ft_iapp_token_nonzero(wire)&&!other.serial);
 assert(wr_ft_auth_request_unpublish_locked(ad,entry,context,&state,&active));
 assert(wr_ft_auth_request_publish_next_locked(ad,entry,context,&state,&active,wire));
 assert(memcmp(wire,first_wire,7)>0);
 assert(wr_ft_auth_request_unpublish_locked(ad,entry,context,&state,&active));
 assert(wr_ft_auth_request_publish_next_locked(ad,entry,context,&state,&active,wire));
 old=active;
 assert(wr_ft_auth_request_admit_locked(ad,entry,context,&state.ledger,wire,
  entry->Addr,entry->wdev->bssid,&active,&claim));
 assert(wr_ft_auth_request_wire_token_locked(ad,entry,context,&state,&active,
  wire,&response_claimed));
 assert(response_claimed&&!wr_ft_iapp_token_nonzero(wire));
 assert(!wr_ft_auth_request_detach_locked(ad,entry,context,&state,&active));
 assert(active.serial==old.serial&&!state.detached[entry->wcid]);
 assert(wr_ft_iapp_token_finish_locked(&state.ledger,&claim));
 assert(wr_ft_auth_request_unpublish_locked(ad,entry,context,&state,&active));
 assert(wr_ft_auth_request_publish_next_locked(ad,entry,context,&state,&active,wire));
 old=active;
 assert(wr_ft_auth_request_detach_locked(ad,entry,context,&state,&active));
 assert(!active.serial&&state.detached[entry->wcid]);
 assert(state.request_by_wcid[entry->wcid].serial==old.serial);
 assert(!wr_ft_auth_request_unpublish_locked(ad,entry,context,&state,&old));
 assert(!wr_ft_auth_request_publish_next_locked(ad,entry,context,&state,&other,wire));
 assert(!wr_ft_iapp_token_nonzero(wire));
 assert(ad->wr_assoc_event_users[entry->wcid]==1);
 {
 struct wr_ft_iapp_token_handle stale=old,detached;
 unsigned char previous[7];
 memcpy(previous,state.ledger.entry[old.slot].token,7);
 assert(!wr_ft_auth_request_retire_detached_locked(ad,entry,NULL,&state,&old));
 assert(!wr_ft_auth_request_retire_detached_locked(ad,entry,context,&state,&state.request_by_wcid[entry->wcid]));
 old.serial++;
 assert(!wr_ft_auth_request_retire_detached_locked(ad,entry,context,&state,&old));
 old=stale;
 assert(wr_ft_auth_request_retire_detached_locked(ad,entry,context,&state,&old));
 assert(!state.detached[entry->wcid]&&!state.request_by_wcid[entry->wcid].serial);
 assert(!wr_ft_iapp_token_claim_locked(&state.ledger,previous,entry->Addr,entry->wdev->bssid,&claim));
 assert(wr_ft_auth_request_publish_next_locked(ad,entry,context,&state,&active,wire));
 assert(memcmp(wire,previous,7)>0);
 assert(wr_ft_auth_request_detach_locked(ad,entry,context,&state,&active));
 detached=state.request_by_wcid[entry->wcid];
 assert(!wr_ft_auth_request_retire_detached_locked(ad,entry,context,&state,&stale));
 assert(state.request_by_wcid[entry->wcid].serial==detached.serial);
 assert(wr_ft_iapp_token_claim_locked(&state.ledger,wire,entry->Addr,entry->wdev->bssid,&claim));
 assert(!wr_ft_auth_request_retire_detached_locked(ad,entry,context,&state,&detached));
 assert(state.request_by_wcid[entry->wcid].serial==detached.serial);
 assert(wr_ft_iapp_token_finish_locked(&state.ledger,&claim));
 }
 }
 }
 NdisReleaseSpinLock(&ad->MacTabLock);
 auth_calls++;
 if(exhaust_generation)ad->wr_assoc_generations[entry->wcid]=~0U;
 return auth_result;
}
'''
actors = actors[:start]+validation_actor+handler+actors[end:]
actors = actors.replace('auth_info={.auth_alg=AUTH_MODE_FT};',
    'auth_info={.auth_alg=AUTH_MODE_FT,.FtInfo={.MdIeInfo={.Len=3},.RSNIE_Len=1}};')
extra = r'''
static void native_handler_refusals(void){
 (void)fallback_calls;(void)APMsgTypeSubst;(void)EAPMlmeQueueFull;
 (void)MlmeQueueFull;(void)wr_assoc_publish;
 RTMP_ADAPTER ad={0};FT_INFO in={0},out={0};
 struct wr_ft_peer_scope scope={0};struct wr_ft_peer_stamp stamp={0};
 struct wr_ft_auth_request_context context={&scope,NULL};
 MAC_TABLE_ENTRY *entry=&ad.MacTab.Content[7];
 ad.ApCfg.BssidNum=3;
 *entry=(MAC_TABLE_ENTRY){.assoc_gen=1,.wcid=7,.func_tb_idx=2,.Sst=SST_ASSOC,
  .client=1,.Addr={42},.wdev=&ad.ApCfg.MBSSID[2].wdev};
 ad.wr_assoc_generations[7]=ad.wr_assoc_visible[7]=1;ad.wr_assoc_addr[7][0]=42;
 stamp=(struct wr_ft_peer_stamp){.generation=1,.wcid=7,.bss=2,.addr={42}};
 NdisAcquireSpinLock(&ad.MacTabLock);
 assert(wr_ft_peer_enter_locked(&ad,&stamp,&scope));
 NdisReleaseSpinLock(&ad.MacTabLock);
 auth_calls=0;exhaust_generation=0;
 assert(FT_AuthReqHandler(NULL,entry,&in,&out,&context)==MLME_FAIL_NO_RESOURCE);
 assert(FT_AuthReqHandler(&ad,NULL,&in,&out,&context)==MLME_FAIL_NO_RESOURCE);
 assert(FT_AuthReqHandler(&ad,entry,&in,&out,NULL)==MLME_FAIL_NO_RESOURCE);
 assert(FT_AuthReqHandler(&ad,&ad.MacTab.Content[1],&in,&out,&context)==MLME_FAIL_NO_RESOURCE);
 scope.stamp.generation++;
 assert(FT_AuthReqHandler(&ad,entry,&in,&out,&context)==MLME_FAIL_NO_RESOURCE);
 scope.stamp.generation--;
 assert(!auth_calls&&!ad.MacTabLock&&entry->assoc_gen==1);
 assert(FT_AuthReqHandler(&ad,entry,&in,&out,&context)==FT_STATUS_CODE_INVALID_MDIE);
 assert(!auth_calls);
 in.MdIeInfo.Len=3;
 assert(FT_AuthReqHandler(&ad,entry,&in,&out,&context)==MLME_SUCCESS);
 assert(!auth_calls&&out.MdIeInfo.Len==3);
 in.RSNIE_Len=1;auth_result=55;
 assert(FT_AuthReqHandler(&ad,entry,&in,&out,&context)==55);
 assert(auth_calls==1&&!ad.MacTabLock&&ad.wr_assoc_event_users[7]==1);
 {
 struct wr_ft_iapp_request_state state;
 struct wr_ft_iapp_token_handle request={0},saved;
 unsigned char seed[7]={0},wire[7];
 wr_ft_iapp_request_state_init(&state);
 assert(wr_ft_iapp_request_state_seed(&state,seed));
 NdisAcquireSpinLock(&ad.MacTabLock);
 assert(wr_ft_auth_request_publish_next_locked(&ad,entry,&context,&state,&request,wire));
 saved=request;
 assert(wr_ft_auth_request_detach_locked(&ad,entry,&context,&state,&request));
 assert(wr_ft_peer_leave_locked(&ad,&scope));
 NdisReleaseSpinLock(&ad.MacTabLock);
 assert(!ad.wr_iot_peer_table_owner.transactions&&!ad.wr_assoc_event_users[7]);
 assert(!scope.active&&!request.serial&&state.detached[7]);
 assert(state.request_by_wcid[7].serial==saved.serial);
 assert(state.ledger.entry[saved.slot].state==WR_FT_IAPP_TOKEN_WAITING);
 assert(wr_ft_iapp_token_equal(state.ledger.entry[saved.slot].token,wire));
 }
}
int main(void){int result=callback_cases();native_handler_refusals();return result;}
'''
with tempfile.TemporaryDirectory(prefix='ft-auth-native-handler-') as td:
    source = Path(td)/'check.c'
    exe = Path(td)/'check'
    source.write_text(prefix+actors+fixture['main'].replace('int main(void)',
                     'static int callback_cases(void)')+extra)
    subprocess.run(['gcc', '-std=gnu11', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-I'+str(here), str(source), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
    for name in ('check-ft-iapp-request-state', 'check-ft-iapp-detached-admission'):
        helper_exe = Path(td)/name
        subprocess.run(['gcc', '-std=gnu11', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                        '-I'+str(here), str(here/(name+'.c')),
                        '-o', str(helper_exe)], check=True)
        subprocess.run([str(helper_exe)], check=True)
print('PASS | FT AUTH invocation context | both caller scopes threaded to native handler and RSN validation; matching declarations; drift and duplicate refusal')
print('PASS | FT AUTH context admission | exact existing/first-peer lease; missing, dual, foreign entry, stale generation and foreign adapter refused; ASan/UBSan callback fixture')
print('PASS | native FT AUTH handler | full composed body; existing/first-peer callback exits; null/stale/foreign context before entry access; MDIE refusal, open and RSN actor paths; ASan/UBSan')
print('PASS | FT invocation request lifecycle | existing/pending begin-admit-end; active handle preserved; claimed response blocks end; timeout cancels delayed response; no peer lease release')
print('PASS | FT adapter request registry | fresh-allocation init only; value handles; active/aliased publication refused; claimed response blocks unpublish; stale invocation cannot clear reused slot; serial retained')
print('PASS | FT wire token publication | seeded sequence; output only after handle publication; failed publication clears wire output; retry never reuses token')
print('PASS | FT soft-retry detach | existing/pending value-handle transfer; claimed response blocks detach; stale cleanup cannot cancel detached request; peer lease releases while exact-generation token remains waiting')
print('PASS | FT detached retry retirement | exact owning context and copied serial required; WAITING cancellation rejects old response; fresh token advances; stale serial and CLAIMED response preserved')
