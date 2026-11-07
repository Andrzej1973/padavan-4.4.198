#!/usr/bin/env python3
"""Inventory vendor MCU wait/ACK intent and execute actual TXD/RX routing on host.

This is source/host evidence, not a firmware, DMA, concurrency or device test.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('driver', type=Path)
p.add_argument('--candidate', type=Path)
p.add_argument('--check', action='store_true')
a = p.parse_args()

def function(text, signature):
    start = text.index(signature)
    end = text.index('\n}\n', start) + 3
    return text[start:end]

def calls(text):
    # Initializer arguments contain balanced C expressions; commas in strings
    # or nested calls are not delimiters. Definition has typed args, excluded.
    clean = re.sub(r'/\*.*?\*/|//[^\n]*', lambda m: '\n' * m.group().count('\n'), text, flags=re.S)
    for match in re.finditer(r'\bAndesInitCmdMsg\s*\(', clean):
        start = match.end(); depth = 0; quote = None; escaped = False; parts = []; last = start
        for pos in range(start, len(clean)):
            ch = clean[pos]
            if quote:
                if escaped: escaped = False
                elif ch == '\\': escaped = True
                elif ch == quote: quote = None
                continue
            if ch in ('"', "'"): quote = ch
            elif ch == '(': depth += 1
            elif ch == ')':
                if not depth:
                    parts.append(clean[last:pos].strip()); break
                depth -= 1
            elif ch == ',' and not depth:
                parts.append(clean[last:pos].strip()); last = pos + 1
        if len(parts) == 12 and 'struct cmd_msg' not in parts[0]:
            # Original source offset via ordered initializer occurrence.
            yield parts, clean.count("\n", 0, match.start()) + 1

mt = (a.driver / 'mcu/andes_mt.c').read_text()
core = (a.driver / 'mcu/andes_core.c').read_text()
sdk = (a.driver / 'include/mcu/andes_mt.h').read_text()
header = function(mt, 'VOID AndesMTFillCmdHeader(')
rx = function(mt, 'static VOID AndesMTRxProcessEvent(')
inventory = []
for path in sorted(a.driver.rglob('*.c')):
    text = path.read_text(errors='replace')
    for number, (args, line) in enumerate(calls(text), 1):
        inventory.append({'path': str(path.relative_to(a.driver)),
                          'initializer_index': number, 'line': line, 'command': args[2],
                          'extended_command': args[4], 'need_wait': args[5],
                          'need_rsp': args[8], 'retransmit': args[7]})
no_wait_ack = [x for x in inventory if x['need_wait'] in ('FALSE', '0') and x['need_rsp'] in ('TRUE', '1')]
assert 'msg->need_rsp == TRUE' in header
assert re.search(r'else\s+msg->seq = 0;', core)
assert 'event_rxd->fw_rxd_1.field.seq_num == 0' in rx
assert 'UnsolicitedEventHandler(' in rx
candidate_header_equal = None
if a.candidate:
    candidate_header_equal = header == function((a.candidate / 'mcu/andes_mt.c').read_text(), 'VOID AndesMTFillCmdHeader(')
    assert candidate_header_equal, 'Candidate TXD policy changed; review before reusing conclusion'
result = {'driver': str(a.driver.resolve()),
          'source_sha256': {name: hashlib.sha256((a.driver / name).read_bytes()).hexdigest()
                            for name in ['mcu/andes_mt.c', 'mcu/andes_core.c', 'include/mcu/andes_mt.h']},
          'candidate_header_equal': candidate_header_equal,
          'candidate_source_sha256': ({name: hashlib.sha256((a.candidate/name).read_bytes()).hexdigest() for name in ['mcu/andes_core.c','mcu/andes_mt.c','include/mcu-sequence-reservation.h']} if a.candidate else None),
          'initializers': inventory, 'explicit_no_wait_with_ack': no_wait_ack,
          'limits': 'Unpreprocessed C inventory includes feature/other-chip branches; dynamic flags and effective board reachability need separate review.',
          'runtime_verified': False}
if a.check:
    tx_start = sdk.rfind('#ifdef RT_BIG_ENDIAN', 0, sdk.index('union _FW_TXD_0'))
    tx_end = sdk.index('} FW_TXD;', tx_start) + len('} FW_TXD;')
    rx_start = sdk.rfind('#ifdef RT_BIG_ENDIAN', 0, sdk.index('union _FW_RXD_0'))
    rx_end = sdk.index('} EVENT_RXD;', rx_start) + len('} EVENT_RXD;')
    prefix = r'''
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
typedef uint32_t UINT32;typedef unsigned char UINT8,UCHAR;typedef void VOID;
#define GNU_PACKED __attribute__((packed))
#define TRUE 1
#define FALSE 0
#define CMD_SET 1
#define CMD_QUERY 0
#define EXT_CID 0xed
#define FW_NO_INIT 0
#define FW_DOWNLOAD 1
#define ROM_PATCH_DOWNLOAD 2
#define FW_RUN_TIME 3
#define EXT_EVENT_FW_LOG_2_HOST 0x13
#define EXT_EVENT_THERMAL_PROTECT 0x22
#define MT_FW_START_RSP 1
#define MT_RESTART_DL_RSP 2
#define MT_TARGET_ADDRESS_LEN_RSP 3
#define MT_PATCH_SEM_RSP 4
#define RTMP_PCI_SUPPORT 1
#define DBGPRINT(level,args) ((void)0)
#define DBGPRINT_S(level,args) ((void)0)
#define cpu2le32(x) (x)
#define le2cpu32(x) (x)
struct packet {unsigned char raw[128];unsigned len;};
typedef struct packet *PNDIS_PACKET;
struct cmd_msg {void *priv;PNDIS_PACKET net_pkt;unsigned pq_id,cmd_type,set_query,seq,ext_cmd_type,need_wait,need_rsp,rsp_payload_len,ack_done;void(*rsp_handler)(struct cmd_msg*,void*,unsigned);};
struct queue {struct cmd_msg *msg;};
struct MCU_CTRL {int Stage,ackq_lock;struct queue ackq;};
typedef struct {struct MCU_CTRL MCUCtrl;} RTMP_ADAPTER;
static void *extend(PNDIS_PACKET p,unsigned n){p->len+=n;return p->raw;}
#define OS_PKT_HEAD_BUF_EXTEND(p,n) extend(p,n)
#define GET_OS_PKT_LEN(p) ((p)->len)
#define GET_OS_PKT_DATAPTR(p) ((p)->raw)
static unsigned unsolicited,completed,callbacks,held;
#define RTMP_SPIN_LOCK_IRQSAVE(lock,flags) do{(void)(lock);*(flags)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(lock,flags) do{(void)(lock);(void)(flags);assert(held);held=0;}while(0)
#define DlListForEachSafe(m,t,q,type,member) for((m)=(q)->msg,(t)=NULL;(void)(t),(m);(m)=NULL)
#define RTMP_OS_COMPLETE(p) (++*(p),++completed)
static void AndesFreeCmdMsg(struct cmd_msg *m){(void)m;assert(0);}
static void UnsolicitedEventHandler(RTMP_ADAPTER *a,UINT8 id,UINT8 ext,UINT8 *data,UINT32 n){(void)a;(void)id;(void)ext;(void)data;(void)n;unsolicited++;}
static void callback(struct cmd_msg *m,void *d,unsigned n){(void)m;(void)d;assert(n==8);callbacks++;}
'''
    main = r'''
int main(void){
 RTMP_ADAPTER ad={0};
 for(unsigned stage=0;stage<4;stage++)for(unsigned wait=0;wait<2;wait++)for(unsigned rsp=0;rsp<2;rsp++)for(unsigned query=0;query<3;query++)for(unsigned ext=0;ext<2;ext++){
  struct packet packet={.len=4};struct cmd_msg msg={.priv=&ad,.need_wait=wait,.need_rsp=rsp,.cmd_type=ext?0xed:1,.set_query=query,.seq=wait?7:0};
  ad.MCUCtrl.Stage=stage;AndesMTFillCmdHeader(&msg,&packet);FW_TXD *tx=(void*)packet.raw;
  assert(tx->fw_txd_2.field.ext_cid_option==(ext&&query<2&&rsp));
  assert(tx->fw_txd_1.field.seq_num==(wait?7:0));
 }
 struct packet event={.len=sizeof(EVENT_RXD)+8};EVENT_RXD *ev=(void*)event.raw;
 struct cmd_msg waiting={.seq=7,.need_wait=1,.rsp_payload_len=8,.rsp_handler=callback};
 struct cmd_msg received={.net_pkt=&event};ad.MCUCtrl.ackq.msg=&waiting;
 ev->fw_rxd_0.field.length=event.len;ev->fw_rxd_1.field.eid=0xed;
 for(unsigned n=0;n<10000;n++)AndesMTRxProcessEvent(&ad,&received);
 assert(unsolicited==10000&&!completed&&!callbacks&&!held);
 ev->fw_rxd_1.field.seq_num=7;AndesMTRxProcessEvent(&ad,&received);
 assert(completed==1&&callbacks==1&&waiting.ack_done==1&&!held);
 puts("PASS actual vendor TXD 96 combinations; 10000 sequence-zero events take unsolicited path without completing pending sequence7; matching reply completes it. Locks, transport and event freeing injected/not exercised.");
}
'''
    if a.candidate:
        prefix = '#include "mcu-sequence-reservation.h"\n' + prefix
        budget = r"""
 for(unsigned region=0;region<2;region++)for(unsigned cycle=0;cycle<3;cycle++){
  /* New host object per iteration, NOT a production restart/reset API. */
  struct wr_iot_mcu_sequence_reservation ledger={0};
  for(unsigned boot=0;boot<2;boot++){
   unsigned id=wr_iot_mcu_sequence_reserve_checked(&ledger);assert(id);
   assert(wr_iot_mcu_sequence_finish(&ledger,id,0));
  }
  unsigned successes=0,failed_channel=0,failed_phase=0;
  unsigned channels=region?13:11;
  for(unsigned channel=1;channel<=channels&&!failed_channel;channel++)for(unsigned phase=0;phase<2;phase++){
   unsigned id=wr_iot_mcu_sequence_reserve_checked(&ledger);
   if(!id){failed_channel=channel;failed_phase=phase;break;}
   assert(wr_iot_mcu_sequence_finish(&ledger,id,0));successes++;
  }
  assert(successes==13&&failed_channel==7&&failed_phase==1);
  assert(!ledger.occupied&&!ledger.quarantined&&ledger.retired==0xfffeU);
 }
 struct wr_iot_mcu_sequence_reservation cancelled={0};
 unsigned cancelled_id=wr_iot_mcu_sequence_reserve_checked(&cancelled);assert(cancelled_id);
 assert(wr_iot_mcu_sequence_finish(&cancelled,cancelled_id,0));
 assert(!cancelled.occupied&&cancelled.retired==(1u<<cancelled_id));
 unsigned timed=wr_iot_mcu_sequence_reserve_checked(&cancelled);assert(timed);
 assert(wr_iot_mcu_sequence_finish(&cancelled,timed,1));
 assert(!cancelled.occupied&&cancelled.quarantined==(1u<<timed));
 puts("PASS actual candidate ledger: repeated host-only11/13-channel models exhaust despite zero occupied IDs; timeout quarantined, cancelled allocation retained. Not device restart or full channel execution.");
"""
        main = main.replace(' puts("PASS actual vendor TXD', budget + ' puts("PASS actual vendor TXD')
    with tempfile.TemporaryDirectory(prefix='wr-ack-intent-') as td:
        c = Path(td) / 'check.c'; c.write_text(prefix + sdk[tx_start:tx_end] + '\n' + sdk[rx_start:rx_end] + '\n' + header + '\n' + rx + main)
        subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined', '-fno-pie', '-no-pie', *(['-I'+str(a.candidate/'include')] if a.candidate else []), str(c), '-o', td+'/check'], check=True)
        result['host_check'] = subprocess.check_output([td+'/check'], text=True).strip()
print(json.dumps(result, indent=2))
