#!/usr/bin/env python3
"""Execute config owner/transport and actual MAC/RF builders; hardware injected."""
import argparse
import ast
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
 'unsigned wr_iot_boot_config_state,wr_iot_boot_active,wr_iot_boot_failed,wr_iot_boot_scheduler_state,wr_iot_boot_fw_state,bPCIclkOff;unsigned long wr_iot_boot_fw_radio_serial,wr_iot_boot_fw_radio_epoch;struct task_struct *wr_iot_boot_config_task;int wr_iot_mcu_sender_wait;struct {int (*pci_kick_out_cmd_msg)(void *,void *);} chipOps;struct wr_iot_mcu_boot_ticket ticket;')
prefix=prefix.replace('*(f)=0;assert(held==1);held=2;', '*(f)=held;assert(held<=1);held=2;')
prefix=prefix.replace('assert(held==2);held=1;', 'assert(held==2);held=*(f);')
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
#define EXT_CMD_RADIO_ON_OFF_CTRL 5
#define CMD_SET 1
#define P1_Q0 0
#define TRUE 1
#define FALSE 0
#define NDIS_STATUS_RESOURCES 2
#define MAC_CR 0
#define RF_CR 1
#define cpu2le32(x) (x)
#define DBGPRINT(level,args) ((void)0)
typedef unsigned UINT32;typedef int INT32;typedef unsigned short UINT16;typedef unsigned char UINT8;typedef int BOOLEAN;typedef void VOID;typedef void (*MSG_RSP_HANDLER)(void);
struct task_struct {unsigned refs;};static struct task_struct owner,foreign,*current;
static void get_task_struct(struct task_struct *t){assert(t&&!held);t->refs++;}
static void put_task_struct(struct task_struct *t){assert(t&&!held&&t->refs);t->refs--;}
struct cmd_msg {void *priv;unsigned wr_iot_config_owned,cmd_type,ext_cmd_type,set_query,need_wait,need_rsp,need_retransmit,rsp_payload_len,wr_iot_checked,used,pq_id,wr_iot_response_done,wr_iot_unsubmitted,wr_iot_firmware_result,timeout,retransmit_times,ack_done;char *rsp_payload;MSG_RSP_HANDLER rsp_handler;unsigned long wr_iot_config_peer_serial,wr_iot_config_radio_serial,wr_iot_config_radio_epoch,wr_iot_config_close_serial,wr_iot_config_close_epoch;unsigned char payload[64];};
static int checked_policy(RTMP_ADAPTER *,struct cmd_msg *);
static unsigned alloc_fail,allocated,freed,sent,ordinary_alloc,ordinary_send,defer_free,wait_timeout;static int transport_result;static struct cmd_msg *pending;
static int AndesMTPciKickOutCmdMsg(void *ad,void *msg){assert(ad&&msg);return 0;}
static void wr_iot_mcu_message_drop(RTMP_ADAPTER *ad,unsigned slot,unsigned uncertain){assert(ad&&!held&&!slot&&!uncertain&&ad->wr_iot_mcu_sender_owner.messages);ad->wr_iot_mcu_sender_owner.messages--;}
static struct cmd_msg *wr_iot_mcu_alloc_body(RTMP_ADAPTER *ad,unsigned length){assert(ad&&!held&&length<=MT_UPLOAD_FW_UNIT&&ad->wr_iot_mcu_sender_owner.messages==1);allocated++;if(alloc_fail)return NULL;struct cmd_msg *m=calloc(1,sizeof(*m));assert(m);m->priv=ad;return m;}
static void AndesForceFreeCmdMsg(struct cmd_msg *m){assert(m&&!held);wr_iot_mcu_message_drop(m->priv,0,0);freed++;free(m);}
static int wr_iot_mcu_send_body(RTMP_ADAPTER *ad,struct cmd_msg *m){assert(ad&&!held&&ad->wr_iot_mcu_sender_owner.inflight==1&&ad->wr_iot_mcu_sender_owner.radio_active&&m->wr_iot_checked&&!checked_policy(ad,m));sent++;if(defer_free)pending=m;else AndesForceFreeCmdMsg(m);return transport_result;}
static int fake_wait(void){assert(!held);if(pending&&!wait_timeout){AndesForceFreeCmdMsg(pending);pending=NULL;}return !wait_timeout;}
#define msecs_to_jiffies(n) (n)
#define wait_event_timeout(q,condition,timeout) ((void)(q),assert((timeout)==5000),fake_wait()?(condition):0)
static int wr_iot_mcu_sender_leave(__typeof__(((RTMP_ADAPTER *)0)->wr_iot_mcu_sender_owner) *s){assert(held==2&&s->inflight==1);s->inflight--;return 1;}
#define wake_up_all(q) ((void)(q),assert(held==2))
typedef struct {UINT32 u4Type,u4Addr,u4Data;} CMD_MULTI_CR_ACCESS_T;
typedef struct {UINT32 Register,Value;} RTMP_REG_PAIR;
typedef struct {UINT32 WiFiStream,Register,Value;} MT_RF_REG_PAIR;
static void CmdMultipleMacRegAccessWriteCb(void){}
static void CmdMultipleRfRegAccessWriteCb(void){}
static struct cmd_msg *AndesAllocCmdMsg(RTMP_ADAPTER *ad,unsigned length){ordinary_alloc++;ad->wr_iot_mcu_sender_owner.messages++;return wr_iot_mcu_alloc_body(ad,length);}
static int AndesSendCmdMsg(RTMP_ADAPTER *ad,struct cmd_msg *m){assert(ad&&!m->wr_iot_config_owned);ordinary_send++;AndesForceFreeCmdMsg(m);return 0;}
#define RTMP_OS_INIT_COMPLETION(p) (*(p)=0)
static void AndesAppendCmdMsg(struct cmd_msg *m,char *p,unsigned length){assert(m->used+length<=sizeof(m->payload));memcpy(m->payload+m->used,p,length);m->used+=length;}
'''
core=(a.candidate/'mcu/andes_core.c').read_text();start=core.index('if (!need_wait || msg->need_retransmit ||')
condition=core[start:core.index(') {',start)+1]
prefix+='\nstatic int checked_policy(RTMP_ADAPTER *ad,struct cmd_msg *msg){\n int need_wait=msg->need_wait;\n '+condition+' {return 1;}\n return 0;\n}\n'
start=core.index('VOID AndesInitCmdMsg(')
prefix+='\n#pragma GCC diagnostic push\n#pragma GCC diagnostic ignored "-Wunused-parameter"\n'+core[start:core.index('\n}\n',start)+3]+'\n#pragma GCC diagnostic pop\n'
mt=(a.candidate/'mcu/andes_mt.c').read_text();builders=[]
for name in ['CmdMultipleMacRegAccessWrite','CmdMultipleRfRegAccessWrite']:
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
with tempfile.TemporaryDirectory(prefix='wr-config-transport-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+(a.candidate/'include/wr-iot-mcu-boot-config-owner.inc').read_text()+(a.candidate/'include/wr-iot-mcu-config-transport.inc').read_text()+'\n'.join(builders)+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
