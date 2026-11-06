#!/usr/bin/env python3
"""Execute config owner/transport and actual MAC/RF builders; hardware injected."""
import argparse
import ast
import json
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
tree=ast.parse(Path(__file__).with_name('check-mcu-boot-retired-boundary.py').read_text())
prefix=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prefix' for t in n.targets))
prefix=prefix[:prefix.index('static int wr_iot_mcu_boot_pse_empty')]
prefix=prefix.replace('static unsigned held, pse_ok, peer_ok, drift_after_pse;','static unsigned held,peer_ok;')
prefix=prefix.replace('typedef struct { unsigned flags; } MCU;', 'typedef struct { unsigned flags,Stage; } MCU;')
prefix=prefix.replace('struct {unsigned messages;}', 'struct {unsigned messages,inflight,radio_active,uncertain;}')
prefix=prefix.replace('struct wr_iot_mcu_boot_ticket ticket;',
 'unsigned wr_iot_boot_config_state,wr_iot_boot_config_unconfirmed,wr_iot_boot_active,wr_iot_boot_failed,wr_iot_boot_scheduler_state,wr_iot_boot_fw_state,bPCIclkOff;unsigned long wr_iot_boot_fw_radio_serial,wr_iot_boot_fw_radio_epoch;struct task_struct *wr_iot_boot_config_task;int wr_iot_mcu_sender_wait;struct {int (*pci_kick_out_cmd_msg)(void *,void *);} chipOps;struct wr_iot_mcu_boot_ticket ticket;')
prefix=prefix.replace('*(f)=0;assert(held==1);held=2;', '*(f)=held;assert(held<=1);held=2;')
prefix=prefix.replace('assert(held==2);held=1;', 'assert(held==2);held=*(f);')
rf_pending=(a.candidate/'include/mcu-config-rf-pending.h').exists()
rf_read=(a.candidate/'include/wr-iot-mcu-config-rf-read.inc').exists()
mac_read=(a.candidate/'include/wr-iot-mcu-config-mac-read.inc').exists()
mac_pending='wr_iot_config_mac_pending' in (a.candidate/'include/rtmp.h').read_text()
if rf_pending:
 prefix='#include "mcu-config-rf-pending.h"\n'+prefix
 prefix=prefix.replace('struct wr_iot_mcu_boot_ticket ticket;',
  'struct wr_iot_config_rf_pending wr_iot_config_rf_pending;struct wr_iot_mcu_boot_ticket ticket;')
if mac_pending:
 prefix=prefix.replace('struct wr_iot_mcu_boot_ticket ticket;',
  'struct wr_iot_config_rf_pending wr_iot_config_mac_pending;struct wr_iot_mcu_boot_ticket ticket;')
prefix+=r'''
#include <stdlib.h>
#include "mcu-config-result.h"
#include "mcu-boot-result.h"
#define wr_iot_boot_ticket ticket
#define FW_RUN_TIME 3
#define fRTMP_ADAPTER_SUSPEND 8u
#define MT_UPLOAD_FW_UNIT 4096
#define EXT_CID 0xed
#define EXT_CMD_MULTIPLE_REG_ACCESS 0x0e
#define CMD_ACCESS_REG 0xc2
#define EXT_CMD_NA 0
#define EXT_CMD_RF_REG_ACCESS 2
#define EXT_CMD_RADIO_ON_OFF_CTRL 5
#define CMD_SET 1
#define CMD_QUERY 0
#define P1_Q0 0
#define TRUE 1
#define FALSE 0
#define NDIS_STATUS_RESOURCES 2
#define MAC_CR 0
#define RF_CR 1
#define cpu2le32(x) (x)
#define DBGPRINT(level,args) ((void)0)
typedef unsigned UINT32;typedef int INT32;typedef unsigned short UINT16;typedef unsigned char UINT8;typedef char CHAR;typedef int BOOLEAN;typedef void VOID;typedef void (*MSG_RSP_HANDLER)(void);
struct task_struct {unsigned refs;};static struct task_struct owner,foreign,*current;
static void get_task_struct(struct task_struct *t){assert(t&&!held);t->refs++;}
static void put_task_struct(struct task_struct *t){assert(t&&!held&&t->refs);t->refs--;}
struct cmd_msg {void *priv,*net_pkt;unsigned wr_iot_config_mac_query,wr_iot_config_mac_generation,wr_iot_config_mac_write,wr_iot_config_mac_address,wr_iot_config_mac_value,wr_iot_config_rf_query,wr_iot_config_rf_generation,wr_iot_config_rf_write,wr_iot_config_rf_stream,wr_iot_config_rf_address,wr_iot_config_rf_value;unsigned wr_iot_config_owned,cmd_type,ext_cmd_type,set_query,need_wait,need_rsp,need_retransmit,rsp_payload_len,wr_iot_checked,used,pq_id,wr_iot_response_done,wr_iot_unsubmitted,wr_iot_firmware_result,timeout,retransmit_times,ack_done;char *rsp_payload;MSG_RSP_HANDLER rsp_handler;unsigned long wr_iot_config_peer_serial,wr_iot_config_radio_serial,wr_iot_config_radio_epoch,wr_iot_config_close_serial,wr_iot_config_close_epoch;unsigned char payload[64];};
#define GET_OS_PKT_LEN(p) (((struct cmd_msg *)(p))->used)
#define GET_OS_PKT_DATAPTR(p) (((struct cmd_msg *)(p))->payload)
static int checked_policy(RTMP_ADAPTER *,struct cmd_msg *);
static unsigned alloc_fail,allocated,freed,sent,ordinary_alloc,ordinary_send,defer_free,wait_timeout,read_mode;static int transport_result;static struct cmd_msg *pending;
static void store_word(unsigned char *p,unsigned v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);}
static int AndesMTPciKickOutCmdMsg(void *ad,void *msg){assert(ad&&msg);return 0;}
static void wr_iot_mcu_message_drop(RTMP_ADAPTER *ad,unsigned slot,unsigned uncertain){assert(ad&&!held&&!slot&&!uncertain&&ad->wr_iot_mcu_sender_owner.messages);ad->wr_iot_mcu_sender_owner.messages--;}
static struct cmd_msg *wr_iot_mcu_alloc_body(RTMP_ADAPTER *ad,unsigned length){assert(ad&&!held&&length<=MT_UPLOAD_FW_UNIT&&ad->wr_iot_mcu_sender_owner.messages==1);allocated++;if(alloc_fail)return NULL;struct cmd_msg *m=calloc(1,sizeof(*m));assert(m);m->priv=ad;m->net_pkt=m;return m;}
static void AndesForceFreeCmdMsg(struct cmd_msg *m){assert(m&&!held);wr_iot_mcu_message_drop(m->priv,0,0);freed++;free(m);}
static int wr_iot_mcu_send_body(RTMP_ADAPTER *ad,struct cmd_msg *m){assert(ad&&!held&&ad->wr_iot_mcu_sender_owner.inflight==1&&ad->wr_iot_mcu_sender_owner.radio_active);if(m->need_wait)assert(m->wr_iot_checked&&!checked_policy(ad,m));else assert(!m->wr_iot_checked&&!m->need_rsp&&!m->rsp_payload_len);sent++;int result=transport_result;if(m->wr_iot_config_rf_query){unsigned char data[12];store_word(data,m->wr_iot_config_rf_stream);store_word(data+4,m->wr_iot_config_rf_address);store_word(data+8,m->wr_iot_config_rf_value);if(read_mode==1)data[8]^=1;if(read_mode==2)data[4]^=1;result=wr_iot_config_rf_read_matches(m->cmd_type,m->ext_cmd_type,m->set_query==CMD_QUERY,0xed,2,data,12,24,24,12,m->wr_iot_config_rf_stream,m->wr_iot_config_rf_address,m->wr_iot_config_rf_value)?0:1;RF_DRIFT}MAC_RESPONSE if(defer_free)pending=m;else AndesForceFreeCmdMsg(m);return result;}
static int fake_wait(void){assert(!held);if(pending&&!wait_timeout){AndesForceFreeCmdMsg(pending);pending=NULL;}return !wait_timeout;}
#define msecs_to_jiffies(n) (n)
#define wait_event_timeout(q,condition,timeout) ((void)(q),assert((timeout)==5000),fake_wait()?(condition):0)
static int wr_iot_mcu_sender_leave(__typeof__(((RTMP_ADAPTER *)0)->wr_iot_mcu_sender_owner) *s){assert(held==2&&s->inflight==1);s->inflight--;return 1;}
#define wake_up_all(q) ((void)(q),assert(held==2))
typedef struct {UINT32 u4Type,u4Addr,u4Data;} CMD_MULTI_CR_ACCESS_T;
typedef struct {UINT32 Register,Value;} RTMP_REG_PAIR;
typedef struct {UINT32 WiFiStream,Register,Value;} MT_RF_REG_PAIR;
struct _CMD_ACCESS_REG_T {UINT32 u4Address,u4Data;};
struct _CMD_RF_REG_ACCESS_T {UINT32 WiFiStream,Address,Data;};
static void CmdMultipleMacRegAccessWriteCb(void){}
static void CmdMultipleRfRegAccessWriteCb(void){}
static struct cmd_msg *AndesAllocCmdMsg(RTMP_ADAPTER *ad,unsigned length){ordinary_alloc++;ad->wr_iot_mcu_sender_owner.messages++;return wr_iot_mcu_alloc_body(ad,length);}
static int AndesSendCmdMsg(RTMP_ADAPTER *ad,struct cmd_msg *m){assert(ad&&!m->wr_iot_config_owned);ordinary_send++;AndesForceFreeCmdMsg(m);return 0;}
#define RTMP_OS_INIT_COMPLETION(p) (*(p)=0)
static void AndesAppendCmdMsg(struct cmd_msg *m,char *p,unsigned length){assert(m->used+length<=sizeof(m->payload));memcpy(m->payload+m->used,p,length);m->used+=length;}
'''
core=(a.candidate/'mcu/andes_core.c').read_text();start=core.index('if (!need_wait || msg->need_retransmit ||')
prefix=prefix.replace('MAC_RESPONSE',r"""if(m->wr_iot_config_mac_query){unsigned char data[32]={0};store_word(data+24,m->wr_iot_config_mac_address);store_word(data+28,m->wr_iot_config_mac_value);if(read_mode==1)data[28]^=1;if(read_mode==2)data[24]^=1;if(read_mode==7)data[20]=1;result=wr_iot_config_mac_read_matches(m->cmd_type,m->ext_cmd_type,m->set_query==CMD_QUERY,0xed,0x0e,data,32,44,44,12,m->wr_iot_config_mac_address,m->wr_iot_config_mac_value)?0:1;if(read_mode==3)ad->wr_iot_config_mac_pending.generation++;if(read_mode==4)peer_ok=0;}""" if mac_read else '')
prefix=prefix.replace('RF_DRIFT','if(read_mode==3)ad->wr_iot_config_rf_pending.generation++;if(read_mode==4)peer_ok=0;' if rf_read else '')
condition=core[start:core.index(') {',start)+1]
prefix+='\nstatic int checked_policy(RTMP_ADAPTER *ad,struct cmd_msg *msg){\n int need_wait=msg->need_wait;\n '+condition+' {return 1;}\n return 0;\n}\n'
start=core.index('VOID AndesInitCmdMsg(')
prefix+='\n#pragma GCC diagnostic push\n#pragma GCC diagnostic ignored "-Wunused-parameter"\n'+core[start:core.index('\n}\n',start)+3]+'\n#pragma GCC diagnostic pop\n'
mt=(a.candidate/'mcu/andes_mt.c').read_text();builders=[]
noresponse='mcu_config_noresponse' in json.loads(Path(str(a.candidate)+'.manifest.json').read_text())
names=['CmdMultipleMacRegAccessWrite','CmdMultipleRfRegAccessWrite']
if noresponse:names+=['CmdAccessRegWrite','CmdRFRegAccessWrite']
if rf_read:
 names+=['CmdRFRegAccessRead']
 prefix+='\nstatic void CmdRFRegAccessReadCb(void){}\n'
if mac_read:
 names+=['CmdMultiPleMacRegAccessRead']
 prefix+='\nstatic void CmdMultipleMacRegAccessReadCb(void){}\n'
for name in names:
 start=mt.index('INT32 '+name+'(');builders.append(mt[start:mt.index('\n}\n',start)+3])
tail=r'''
static RTMP_ADAPTER valid(void){RTMP_ADAPTER ad={0};ad.ticket=(struct wr_iot_mcu_boot_ticket){1,2,3,4,5};
 ad.wr_iot_boot_active=ad.wr_iot_boot_frozen=ad.wr_iot_boot_mcu_only=1;ad.wr_iot_boot_hw_state=2;ad.wr_iot_boot_hw_stage=6;
 ad.wr_iot_boot_fw_state=ad.wr_iot_boot_scheduler_state=2;ad.wr_iot_boot_fw_radio_serial=2;ad.wr_iot_boot_fw_radio_epoch=3;
 ad.wr_iot_boot_ctrl_state=ad.wr_iot_boot_rx_state=ad.wr_iot_boot_irq_state=ad.wr_iot_boot_dma_state=ad.wr_iot_boot_irq_unmask_state=2;
 ad.MCUCtrl.Stage=3;ad.chipOps.pci_kick_out_cmd_msg=AndesMTPciKickOutCmdMsg;return ad;}
int main(void){unsigned fault;
for(fault=0;fault<14;fault++){
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;allocated=freed=sent=alloc_fail=0;transport_result=0;
 defer_free=fault>=12;wait_timeout=fault==13;pending=NULL;
 assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));
 if(fault==1)current=&foreign;
 if(fault==2)alloc_fail=1;
 struct cmd_msg *m=wr_iot_mcu_config_alloc(&ad,12);
 if(fault==1||fault==2){assert(!m&&!ad.wr_iot_mcu_sender_owner.messages);current=&owner;}
 else {
 assert(m&&ad.wr_iot_mcu_sender_owner.messages==1);
 assert(!wr_iot_mcu_config_alloc(&ad,12));
 m->cmd_type=EXT_CID;m->ext_cmd_type=EXT_CMD_MULTIPLE_REG_ACCESS;m->set_query=CMD_SET;m->need_wait=m->need_rsp=1;m->rsp_payload_len=32;
 if(!fault){assert(!checked_policy(&ad,m));m->wr_iot_config_owned=0;assert(checked_policy(&ad,m));m->wr_iot_config_owned=1;m->need_rsp=0;assert(checked_policy(&ad,m));m->need_rsp=1;}
 switch(fault){case 3:m->wr_iot_config_close_epoch++;break;case 4:m->need_retransmit=1;break;case 5:m->ext_cmd_type++;break;
 case 6:m->need_rsp=0;break;case 7:m->need_wait=0;break;case 8:m->rsp_payload_len=31;break;case 9:transport_result=-7;break;
 case 10:current=&foreign;break;case 11:ad.chipOps.pci_kick_out_cmd_msg=NULL;break;}
 assert(wr_iot_mcu_config_send(&ad,m)==(fault==9?-7:(!fault||fault==12)?0:1));
 if(fault==13){assert(pending&&freed==0&&ad.wr_iot_mcu_sender_owner.messages==1&&ad.wr_iot_boot_failed&&ad.wr_iot_mcu_sender_owner.uncertain);AndesForceFreeCmdMsg(pending);pending=NULL;}
 assert(freed==1&&!ad.wr_iot_mcu_sender_owner.messages&&!ad.wr_iot_mcu_sender_owner.inflight);
 assert(sent==(!fault||fault==9||fault>=12));current=&owner;
 }
 assert(wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,!fault||fault==12)==((!fault||fault==12)?0:1));assert(!owner.refs&&!foreign.refs&&ad.wr_iot_boot_frozen);
}
for(unsigned owned=0;owned<2;owned++){
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;alloc_fail=defer_free=wait_timeout=0;transport_result=0;ordinary_alloc=ordinary_send=0;
 RTMP_REG_PAIR mac[2]={{1,2},{3,4}};MT_RF_REG_PAIR rf[2]={{1,5,6},{1,7,8}};
 if(owned)assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));else ad.wr_iot_boot_active=0;
 assert(!CmdMultipleMacRegAccessWrite(&ad,mac,2));assert(!CmdMultipleRfRegAccessWrite(&ad,rf,2));
 assert(ordinary_alloc==(owned?0u:2u)&&ordinary_send==(owned?0u:2u));
 if(owned){unsigned before=allocated;assert(CmdMultipleMacRegAccessWrite(&ad,mac,~0u)==1&&allocated==before);assert(!wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1));}
}
puts("PASS owner/config transport + actual MAC/RF builders: exact tickets/task, single constructor, allocation/refusal/transport failures, consumed message lifetime, ordinary routing and oversized bootstrap refusal; SDK transport/locks/ACK result injected");}
'''
if noresponse:
 pos=tail.index('puts("PASS owner/config transport')
 tail=tail[:pos]+r'''
for(unsigned mode=0;mode<3;mode++){
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;alloc_fail=0;transport_result=0;allocated=freed=sent=0;
 defer_free=mode!=0;wait_timeout=mode==2;pending=NULL;
 assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));
 assert(CmdAccessRegWrite(&ad,0x100,0x200)==(mode==2?1:0));
 assert(ad.wr_iot_boot_config_unconfirmed==1);
 if(mode==2){assert(pending&&ad.wr_iot_mcu_sender_owner.messages==1&&ad.wr_iot_mcu_sender_owner.uncertain);AndesForceFreeCmdMsg(pending);pending=NULL;}
 else {assert(!CmdRFRegAccessWrite(&ad,1,2,3));assert(ad.wr_iot_boot_config_unconfirmed==2&&sent==2);}
 assert(wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1)==1);
 assert(ad.wr_iot_boot_config_state==3&&ad.wr_iot_boot_failed&&!owner.refs&&ad.wr_iot_boot_config_unconfirmed);
}
{
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;defer_free=wait_timeout=0;transport_result=0;sent=0;
 assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));ad.wr_iot_boot_config_unconfirmed=~0u;
 assert(CmdAccessRegWrite(&ad,1,2)==1&&!sent&&ad.wr_iot_boot_config_unconfirmed==~0u);
 assert(wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1)==1&&!owner.refs);
}
puts("PASS no-response MAC/RF builders: TX-only result, immediate/delayed/timeout drain, unresolved effects block finish and counter overflow refuses before hardware");
'''+tail[pos:]
if rf_pending:
 tail=tail.replace('assert(ad.wr_iot_boot_config_unconfirmed==2&&sent==2);',
 '''assert(ad.wr_iot_boot_config_unconfirmed==2&&sent==2);
 assert(wr_iot_config_rf_record_matches(&ad.wr_iot_config_rf_pending,1,1,2,3,4,5,1,2,3));
 assert(CmdRFRegAccessWrite(&ad,1,4,5)==1&&sent==2&&ad.wr_iot_boot_config_unconfirmed==2);
 assert(wr_iot_config_rf_record_matches(&ad.wr_iot_config_rf_pending,1,1,2,3,4,5,1,2,3));''')
 pos=tail.index('puts("PASS owner/config transport')
 tail=tail[:pos]+r'''
{
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;alloc_fail=0;defer_free=wait_timeout=1;transport_result=0;pending=NULL;sent=0;
 assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));assert(CmdRFRegAccessWrite(&ad,1,2,3)==1);
 assert(pending&&ad.wr_iot_mcu_sender_owner.messages==1&&ad.wr_iot_boot_config_unconfirmed==1);
 assert(wr_iot_config_rf_record_matches(&ad.wr_iot_config_rf_pending,1,1,2,3,4,5,1,2,3));
 assert(wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1)==1&&!owner.refs);
 AndesForceFreeCmdMsg(pending);pending=NULL;
 assert(ad.wr_iot_config_rf_pending.active&&ad.wr_iot_boot_config_unconfirmed==1);
}
{
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;alloc_fail=defer_free=wait_timeout=0;transport_result=0;sent=0;
 assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));struct cmd_msg *m=wr_iot_mcu_config_alloc(&ad,12);assert(m);
 m->cmd_type=EXT_CID;m->ext_cmd_type=EXT_CMD_RF_REG_ACCESS;m->set_query=CMD_SET;
 m->wr_iot_config_rf_write=1;m->wr_iot_config_rf_stream=1;m->wr_iot_config_rf_address=2;m->wr_iot_config_rf_value=3;
 struct _CMD_RF_REG_ACCESS_T bad={1,2,4};AndesAppendCmdMsg(m,(char *)&bad,sizeof(bad));
 assert(wr_iot_mcu_config_send(&ad,m)==1&&!sent&&!ad.wr_iot_config_rf_pending.active&&!ad.wr_iot_boot_config_unconfirmed);
 assert(wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1)==1&&!owner.refs);
}
puts("PASS actual RF builder records exact serialized payload/full ticket before TX; duplicate write, timeout retention and mismatched metadata refuse");
for(unsigned mode=0;mode<2;mode++){
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;
 assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));
 if(mode)ad.wr_iot_config_rf_pending.poisoned=1;else ad.wr_iot_config_rf_pending.active=1;
 assert(!ad.wr_iot_boot_config_unconfirmed);
 assert(wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1)==1&&!owner.refs&&ad.wr_iot_boot_failed);
}
'''+tail[pos:]
if rf_read:
 pos=tail.index('puts("PASS owner/config transport')
 tail=tail[:pos]+r'''
for(unsigned mode=0;mode<8;mode++){
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;alloc_fail=defer_free=wait_timeout=read_mode=0;transport_result=0;pending=NULL;
 assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));assert(!CmdRFRegAccessWrite(&ad,1,2,0x89abcdefU));
 unsigned output=0x55555555U;read_mode=mode;
 if(mode==5)defer_free=wait_timeout=1;
 if(mode==6)ad.wr_iot_config_rf_pending.active=0;
 int ret=CmdRFRegAccessRead(&ad,1,mode==7?3:2,&output);
 assert(ret==(mode?1:0));
 if(!mode){
 assert(output==0x89abcdefU&&!ad.wr_iot_config_rf_pending.active&&!ad.wr_iot_boot_config_unconfirmed);
 output=9;assert(CmdRFRegAccessRead(&ad,1,2,&output)==1&&output==9);
 assert(!CmdRFRegAccessWrite(&ad,1,2,7)&&ad.wr_iot_config_rf_pending.generation==2);
 assert(!CmdRFRegAccessRead(&ad,1,2,&output)&&output==7&&!ad.wr_iot_boot_config_unconfirmed);
 assert(!wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1));
 }else{
 assert(output==0x55555555U&&ad.wr_iot_boot_config_unconfirmed==1);
 if(mode==5){assert(pending&&ad.wr_iot_mcu_sender_owner.messages==1);AndesForceFreeCmdMsg(pending);pending=NULL;}
 current=&owner;assert(wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,0)==1);
 }
 assert(!owner.refs&&!foreign.refs);
}
{
 RTMP_ADAPTER ad=valid();unsigned output=0;current=&owner;peer_ok=1;alloc_fail=defer_free=wait_timeout=read_mode=0;transport_result=0;
 assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));assert(!CmdAccessRegWrite(&ad,1,2));
 assert(!CmdRFRegAccessWrite(&ad,1,2,3)&&ad.wr_iot_boot_config_unconfirmed==2);
 assert(!CmdRFRegAccessRead(&ad,1,2,&output)&&output==3&&ad.wr_iot_boot_config_unconfirmed==1);
 assert(wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1)==1&&!owner.refs);
}
puts("PASS RF write/read/retirement: exact tuple, stale generation/peer, mismatch/timeout retain proof and output, one counter decrement, duplicate query refusal, next generation and MAC counter preservation; transport ACK injected via real parser");
'''+tail[pos:]
if mac_pending:
 pos=tail.index('puts("PASS owner/config transport')
 tail=tail[:pos]+r'''
{
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;alloc_fail=defer_free=wait_timeout=read_mode=0;transport_result=0;sent=0;
 assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));assert(!CmdAccessRegWrite(&ad,0x1234,0x89abcdefU));
 assert(wr_iot_config_rf_record_matches(&ad.wr_iot_config_mac_pending,1,1,2,3,4,5,0,0x1234,0x89abcdefU));
 assert(CmdAccessRegWrite(&ad,0x1234,1)==1&&sent==1&&ad.wr_iot_boot_config_unconfirmed==1);
 assert(wr_iot_config_rf_record_matches(&ad.wr_iot_config_mac_pending,1,1,2,3,4,5,0,0x1234,0x89abcdefU));
 assert(wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1)==1&&!owner.refs);
}
{
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;alloc_fail=defer_free=wait_timeout=read_mode=0;transport_result=0;sent=0;
 assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));struct cmd_msg *m=wr_iot_mcu_config_alloc(&ad,8);assert(m);
 m->cmd_type=CMD_ACCESS_REG;m->ext_cmd_type=EXT_CMD_NA;m->set_query=CMD_SET;
 m->wr_iot_config_mac_write=1;m->wr_iot_config_mac_address=1;m->wr_iot_config_mac_value=2;
 struct _CMD_ACCESS_REG_T bad={1,3};AndesAppendCmdMsg(m,(char *)&bad,sizeof(bad));
 assert(wr_iot_mcu_config_send(&ad,m)==1&&!sent&&!ad.wr_iot_config_mac_pending.active&&!ad.wr_iot_boot_config_unconfirmed);
 assert(wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1)==1&&!owner.refs);
}
for(unsigned mode=0;mode<2;mode++){
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));
 if(mode)ad.wr_iot_config_mac_pending.poisoned=1;else ad.wr_iot_config_mac_pending.active=1;
 assert(!ad.wr_iot_boot_config_unconfirmed&&wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1)==1&&!owner.refs);
}
puts("PASS exact MAC intent before TX: serialized payload, full ticket, no pending overwrite, mismatched tags and poisoned/pending finish refusal");
'''+tail[pos:]
if mac_read:
 pos=tail.index('puts("PASS owner/config transport')
 tail=tail[:pos]+r'''
for(unsigned mode=0;mode<8;mode++){
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;alloc_fail=defer_free=wait_timeout=read_mode=0;transport_result=0;pending=NULL;
 assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));assert(!CmdAccessRegWrite(&ad,0x1234,0x89abcdefU));
 unsigned output=0x55555555U;read_mode=mode;
 if(mode==5)defer_free=wait_timeout=1;
 if(mode==6)ad.wr_iot_config_mac_pending.active=0;
 RTMP_REG_PAIR pair={0x1234,output};int ret=CmdMultiPleMacRegAccessRead(&ad,&pair,1);output=pair.Value;assert(ret==(mode?1:0));
 if(!mode){
  assert(output==0x89abcdefU&&!ad.wr_iot_config_mac_pending.active&&!ad.wr_iot_boot_config_unconfirmed);
  output=9;assert(wr_iot_mcu_config_mac_read(&ad,0x1234,&output)==1&&output==9);
  assert(!CmdAccessRegWrite(&ad,0x1234,7)&&ad.wr_iot_config_mac_pending.generation==2);
  assert(!wr_iot_mcu_config_mac_read(&ad,0x1234,&output)&&output==7);
  assert(!wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1));
 }else{
  assert(output==0x55555555U&&ad.wr_iot_boot_config_unconfirmed==1);
  if(mode==5){assert(pending);AndesForceFreeCmdMsg(pending);pending=NULL;}
  current=&owner;assert(wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,0)==1);
 }
 assert(!owner.refs&&!foreign.refs);
}
{
 RTMP_ADAPTER ad=valid();current=&owner;peer_ok=1;alloc_fail=defer_free=wait_timeout=read_mode=0;transport_result=0;
 assert(!wr_iot_mcu_boot_config_begin(&ad,&ad.ticket));assert(!CmdAccessRegWrite(&ad,2,3));
 assert(!CmdRFRegAccessWrite(&ad,1,2,7));unsigned output=9;RTMP_REG_PAIR pair={2,9};
 assert(CmdMultiPleMacRegAccessRead(&ad,&pair,2)==1&&pair.Value==9);
 assert(CmdMultiPleMacRegAccessRead(&ad,NULL,1)==1);
 assert(wr_iot_mcu_config_mac_read(&ad,3,&output)==1&&output==9);
 assert(!CmdMultiPleMacRegAccessRead(&ad,&pair,1)&&pair.Value==3);
 assert(ad.wr_iot_boot_config_unconfirmed==1&&ad.wr_iot_config_rf_pending.active);
 assert(!CmdRFRegAccessRead(&ad,1,2,&output)&&output==7&&!ad.wr_iot_boot_config_unconfirmed);
 assert(!wr_iot_mcu_boot_config_finish(&ad,&ad.ticket,1)&&!owner.refs);
}
puts("PASS MAC checked read: exact tuple, type/address/value mismatch, stale generation/peer, timeout, retained output/proof, duplicate refusal and next generation; injected transport");
'''+tail[pos:]
with tempfile.TemporaryDirectory(prefix='wr-config-transport-') as td:
 c=Path(td)/'check.c';reader=(a.candidate/'include/wr-iot-mcu-config-rf-read.inc').read_text() if rf_read else ''
 if mac_read:reader+=(a.candidate/'include/wr-iot-mcu-config-mac-read.inc').read_text()
 c.write_text(prefix+(a.candidate/'include/wr-iot-mcu-boot-config-owner.inc').read_text()+(a.candidate/'include/wr-iot-mcu-config-transport.inc').read_text()+reader+'\n'.join(builders)+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
