#!/usr/bin/env python3
"""Stage checked-only ACK result plumbing, without a live command issuer.

Source tree is never edited. Lifecycle exclusion, full driver compilation and
timeout concurrency tests remain required before production integration.
"""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path, help='mt76x3 directory')
p.add_argument('output', type=Path, help='new separate candidate directory')
a = p.parse_args()
root, out = a.source.resolve(), a.output.resolve()
if out == root or root in out.parents or out in root.parents or a.output.exists():
    raise SystemExit('Output must be new and separate from source')
identities = {
    'include/mcu/andes_core.h': 'ddd27a9cab7f03e22b74116e27bc8e442b573658',
    'mcu/andes_core.c': '6b430c071742b839a77403bf76d5a4f592abc138',
    'mcu/andes_mt.c': 'cd3b3c371a505f510f1081ba6be0585c351f492e',
}
originals = {}
for name, expected in identities.items():
    data = (root / name).read_bytes()
    digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    if digest != expected:
        raise SystemExit('Unreviewed source bytes: ' + name)
    originals[name] = data

def once(text, anchor, replacement):
    if text.count(anchor) != 1:
        raise SystemExit('Changed/duplicated source anchor: ' + anchor[:65])
    return text.replace(anchor, replacement, 1)

texts = {name: data.decode('utf-8') for name, data in originals.items()}
name = 'include/mcu/andes_core.h'
texts[name] = once(texts[name], '\tBOOLEAN need_wait;', '''    /* Opt-in only; initialized disabled for every normal command. */
    BOOLEAN wr_iot_checked;
    BOOLEAN wr_iot_response_done;
    BOOLEAN wr_iot_unsubmitted;
    INT32 wr_iot_firmware_result;
\tBOOLEAN need_wait;''')
name = 'mcu/andes_core.c'
texts[name] = once(texts[name], '\tmsg->need_wait= need_wait;', '''    msg->wr_iot_checked = FALSE;
    msg->wr_iot_response_done = FALSE;
    msg->wr_iot_unsubmitted = FALSE;
    msg->wr_iot_firmware_result = NDIS_STATUS_FAILURE;
\tmsg->need_wait= need_wait;''')
texts[name] = once(texts[name], '''\t\t\tif (!msg->need_wait)
\t\t\t\tAndesForceFreeCmdMsg(msg);
\t\t\tcontinue;''', '''            if (msg->wr_iot_checked && msg->need_wait) {
                msg->wr_iot_unsubmitted = TRUE;
                msg->state = tx_kickout_fail;
                RTMP_OS_COMPLETE(&msg->ack_done);
            } else if (!msg->need_wait) {
                AndesForceFreeCmdMsg(msg);
            }
            continue;''')
texts[name] = once(texts[name], '''\t\t\tif (ret == NDIS_STATUS_FAILURE)
\t\t\t\tAndesForceFreeCmdMsg(msg);''', '''            if (msg->wr_iot_checked && msg->need_wait) {
                /* A nonzero return can precede or follow ring ownership.
                 * Only a positively private packet can be force-freed. */
                if (msg->wr_iot_unsubmitted) {
                    msg->state = tx_kickout_fail;
                    RTMP_OS_COMPLETE(&msg->ack_done);
                }
            } else if (ret == NDIS_STATUS_FAILURE) {
                AndesForceFreeCmdMsg(msg);
            }''')
start = texts[name].index('INT32 AndesSendCmdMsg(')
before, sender = texts[name][:start], texts[name][start:]
sender = once(sender, '\tif(in_interrupt() && need_wait)', '''    if (msg->wr_iot_checked) {
#ifndef RTMP_PCI_SUPPORT
        AndesForceFreeCmdMsg(msg);
        return NDIS_STATUS_FAILURE;
#else
        if (!need_wait || msg->need_retransmit || msg->cmd_type != EXT_CID ||
            msg->ext_cmd_type != EXT_CMD_RADIO_ON_OFF_CTRL ||
            ad->chipOps.pci_kick_out_cmd_msg != AndesMTPciKickOutCmdMsg) {
            AndesForceFreeCmdMsg(msg);
            return NDIS_STATUS_FAILURE;
        }
#endif
    }
\tif(in_interrupt() && need_wait)''')
sender = once(sender, '\n\t\tif (OS_TEST_BIT(MCU_INIT, &ctl->flags)) {', '''
        /* Copy checked status before queue transfer/free. Timeouts never
         * inspect a result that a late response might still be writing. */
        if (!ret && msg->wr_iot_checked)
            ret = state == tx_done && msg->wr_iot_response_done ?
                msg->wr_iot_firmware_result : NDIS_STATUS_FAILURE;
        if (msg->wr_iot_checked && msg->wr_iot_unsubmitted) {
            AndesForceFreeCmdMsg(msg);
            return NDIS_STATUS_FAILURE;
        }
\t\tif (OS_TEST_BIT(MCU_INIT, &ctl->flags)) {''')
texts[name] = before + sender
name = 'mcu/andes_mt.c'
texts[name] = once(texts[name], '#include\t"rt_config.h"', '#include\t"rt_config.h"\n#include "wr-iot-radio-result.h"')
kick_start = texts[name].index('INT32 AndesMTPciKickOutCmdMsg(')
kick_end = texts[name].index('\n}', kick_start) + 2
kick = texts[name][kick_start:kick_end]
check = '\tif (!OS_TEST_BIT(MCU_INIT, &ctl->flags))'
if kick.count(check) != 2:
    raise SystemExit('PCI MCU availability checks changed')
kick = kick.replace(check, '\tif (msg->wr_iot_checked) {\n\t\tmsg->wr_iot_unsubmitted = TRUE;\n\t}\n' + check, 1)
kick = once(kick, '\tpAd->CtrlRing.Cell[SwIdx].pNdisPacket = net_pkt;', '''\tpAd->CtrlRing.Cell[SwIdx].pNdisPacket = net_pkt;
\tif (msg->wr_iot_checked) {
\t\tmsg->wr_iot_unsubmitted = FALSE;
\t}''')
texts[name] = texts[name][:kick_start] + kick + texts[name][kick_end:]
builder = Path(__file__).with_name('checked-radio-off-builder.inc').read_text(encoding='utf-8')
anchor = 'INT32 CmdRadioOnOffCtrl(RTMP_ADAPTER *pAd, UINT8 On)'
texts[name] = once(texts[name], anchor, builder + '\n' + anchor)
branch = '''                if (msg->wr_iot_checked) {
                    /* Still under ackq_lock: only bounded parse and completion,
                     * no generic callback/hook and no stack result pointer. */
                    if (msg->wr_iot_response_done)
                        break;
                    msg->wr_iot_response_done = TRUE;
                    msg->wr_iot_firmware_result = NDIS_STATUS_FAILURE;
                    if (msg->need_wait && msg->cmd_type == EXT_CID &&
                        msg->ext_cmd_type == EXT_CMD_RADIO_ON_OFF_CTRL &&
                        event_rxd->fw_rxd_1.field.eid == EXT_EVENT &&
                        event_rxd->fw_rxd_2.field.ext_eid == EXT_EVENT_CMD_RESULT &&
                        GET_OS_PKT_LEN(net_pkt) == sizeof(*event_rxd) + WR_IOT_RADIO_RESULT_SIZE &&
                        event_rxd->fw_rxd_0.field.length == sizeof(*event_rxd) + WR_IOT_RADIO_RESULT_SIZE &&
                        wr_iot_radio_result_success(GET_OS_PKT_DATAPTR(net_pkt) + sizeof(*event_rxd), WR_IOT_RADIO_RESULT_SIZE))
                        msg->wr_iot_firmware_result = NDIS_STATUS_SUCCESS;
                    if (msg->need_wait)
                        RTMP_OS_COMPLETE(&msg->ack_done);
                    break;
                }
'''
anchor = '\t\t\tif (msg->seq == event_rxd->fw_rxd_1.field.seq_num)\n\t\t\t{'
texts[name] = once(texts[name], anchor, anchor + '\n' + branch)
for name, data in originals.items():
    if (root / name).read_bytes() != data:
        raise SystemExit('Source changed during preparation: ' + name)
out.mkdir()
records = []
for name, text in texts.items():
    target = out / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')
    records.append({'path': name, 'original_git_blob': identities[name],
                    'candidate_sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
parser = Path(__file__).with_name('radio-result.h').read_bytes()
(out / 'mcu/wr-iot-radio-result.h').write_bytes(parser)
(out / 'checked-ack-branch.inc').write_text(branch, encoding='utf-8')
(out / 'manifest.json').write_text(json.dumps({
    'production_installed': False, 'command_issuer_bound': False,
    'target_compiled': False, 'lifecycle_exclusion_proven': False,
    'timeout_concurrency_verified': False, 'files': records,
    'post_ownership_retirement_proven': False,
    'active_waiter_exit_exclusion_proven': False,
    'production_prerequisites': [
        'Serialize checked sender admission against MCU exit and reset.',
        'Drain active waiters before ACK cleanup and spinlock destruction.',
        'Prove DMA stopped before retiring a ring-owned packet on failure.',
        'Reject uncertain completion; never replay a checked request implicitly.',
        'Validate actual target driver and recoverable on-device acceptance.',
    ],
    'parser_sha256': hashlib.sha256(parser).hexdigest(),
    'off_builder_sha256': hashlib.sha256(builder.encode('utf-8')).hexdigest(),
    'off_builder_sends_command': False,
}, indent=2) + '\n', encoding='utf-8')
print('Prepared isolated checked-only ACK plumbing; no command issuer or production installation')
