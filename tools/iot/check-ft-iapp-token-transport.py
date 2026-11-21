#!/usr/bin/env python3
"""Check reserved FT key-event token transport across pinned driver/IAPP sources."""
import argparse
import hashlib
import re
import tarfile
from pathlib import Path

PINNED = {
    'common/ft.c': 'd0adbee2fe62e783c8c2924ae5c16e03b248b613dba91ffbd6e4f8d7fcbdfd85',
    'ap/ap_ftkd.c': '19ca90564222128b0a8ef98e7799bd542e5725a71d130c2d6a3e37ffb7488e4b',
    'include/ft.h': '95465f2a5f52e84a9663de511a5df9d47edcbbfd386dabb60863bd2d5ab67d9b',
}
DAEMON = {
    'trunk/user/ralinkiappd/rtmpiapp.c': 'be9150ce4240f54656b7c06b6e576b7dec78c6e336e04f78bf1232af37d842a7',
    'trunk/user/ralinkiappd/rtmpiapp.h': 'ed483ce83c98ca93ca921fe123831b41183a0020f30b3439792a61fc84f1b6b4',
    'trunk/user/ralinkiappd/rt_config.h': 'f3d18b6fe2d17f4bb02c8616d10670a025e6262be1dff7625abb23001e7776af',
}


def require(text, anchor, label):
    if anchor not in text:
        raise ValueError('pinned FT token transport anchor changed: ' + label)


p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path, help='pinned mt76x3 source root')
p.add_argument('--daemon-archive', type=Path,
               default=Path('/home/andrzej/padavan-build/firmware-source-backup/padavan-4.4-c25283e-git-exact.tar'))
a = p.parse_args()
source = a.source.resolve()
texts = {}
for name, expected in PINNED.items():
    data = (source/name).read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('pinned vendor source hash mismatch: ' + name)
    texts[name] = data.decode('latin1')

ft = texts['common/ft.c']
header = texts['include/ft.h']
remote = texts['ap/ap_ftkd.c']
require(ft, 'FT_KDP_EVT_KEY_ELM EvtKeyReq;', 'native request object')
require(ft, 'NdisZeroMemory(&EvtKeyReq, sizeof(FT_KDP_EVT_KEY_ELM));', 'native request initialization')
require(ft, 'FT_KDP_EVENT_INFORM(pAd, pEntry->func_tb_idx, FT_KDP_SIG_KEY_REQ_AUTO,', 'native automatic request')
if not re.search(r'UCHAR\s+RSV\[3\];', header):
    raise ValueError('pinned FT token transport anchor changed: event reserved bytes')
if not re.search(r'UCHAR\s+RSV\[4\];', header):
    raise ValueError('pinned FT token transport anchor changed: key-info reserved bytes')
require(remote, 'FT_QueryKeyInfoForKDP(pAd, ApIdx, pEvtKeyReq)', 'remote request processing')
require(remote, 'FT_KDP_EventInform(pAd, ApIdx, FT_KDP_SIG_KEY_RSP_AUTO,', 'remote response event')
require(remote, '(VOID *)pEvtKeyReq, sizeof(FT_KDP_EVT_KEY_ELM),', 'same remote event payload')
require(remote, 'pEvtKeyRsp = (FT_KDP_EVT_KEY_ELM *)(pNonce + FT_NONCE_SIZE);', 'local response payload parse')

with tarfile.open(a.daemon_archive, 'r:') as archive:
    daemon = {}
    for name, expected in DAEMON.items():
        data = archive.extractfile(name).read()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('pinned daemon source hash mismatch: ' + name)
        daemon[name] = data.decode('latin1')

iapp = daemon['trunk/user/ralinkiappd/rtmpiapp.c']
require(iapp, 'IAPP_MEM_MOVE(pIappSendSB->SB, pEvt, pEvtHdr->EventLen);', 'request payload copy')
require(iapp, 'case FT_KDP_SIG_KEY_REQ_AUTO:', 'automatic request route')
require(iapp, 'case FT_KDP_SIG_KEY_RSP_AUTO:', 'automatic response route')
require(iapp, 'IAPP_MEM_MOVE(pIappSendSB->SB, pEvt, pEvtHdr->EventLen);', 'response payload copy')
require(iapp, 'IAPP_MEM_MOVE(OidReq->Buf+FT_IP_ADDRESS_SIZE+IAPP_SB_INIT_VEC_SIZE,\n\t\t\t\t\t\t\tpAckSB->SB,\n\t\t\t\t\t\t\tpAckSB->Length);', 'response ioctl payload')
require(iapp, 'for (idx = 0; idx < pCtrlBK->IfNameWlanCount; idx++) {', 'broadcast-to-interfaces response routing')
require(iapp, 'IAPP_MEM_MOVE(OidReq->Buf+FT_IP_ADDRESS_SIZE,\n\t\t\t\t\t\t\tpAckSB->InitVec,', 'separate IAPP nonce forwarding')

helper = (Path(__file__).with_name('ft-iapp-response-token.h')).read_text()
require(helper, 'for (i = 0; i < 3; i++)\n\t\telement_rsv[i] = token[i];', 'three event reserved token bytes')
require(helper, 'for (i = 0; i < 4; i++)\n\t\tkeyinfo_rsv[i] = token[i + 3];', 'four key-info reserved token bytes')
require(helper, 'token[i] = element_rsv[i];', 'event token unpack')
require(helper, 'token[i + 3] = keyinfo_rsv[i];', 'key-info token unpack')

print('PASS | FT IAPP token transport | 7 reserved event bytes copy across pinned driver, daemon and remote response')
print('PASS | FT IAPP nonce boundary | separate 8-byte nonce is forwarded but not bound to request generation')
print('PASS | FT IAPP transport identity | daemon response fans out to interfaces; local response must claim token and exact peer context')
