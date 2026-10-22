#!/usr/bin/env python3
"""Extract actual candidate sender; queue/dispatch/wait operations are injected."""
import argparse
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--with-dispatcher', action='store_true')
a = p.parse_args()
if a.output.exists():
    raise SystemExit('Refusing to overwrite output')
source = (a.candidate / 'mcu/andes_core.c').read_text(encoding='utf-8')
anchor = 'INT32 AndesSendCmdMsg(PRTMP_ADAPTER ad, struct cmd_msg *msg)'
if source.count(anchor) != 1:
    raise SystemExit('Sender signature changed')
start = source.index(anchor)
end = source.index('\n}', start) + 2
sender = source[start:end]
prefix = r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int INT32;
typedef int BOOLEAN;
#define RTMP_PCI_SUPPORT 1
typedef void *PNDIS_PACKET;
enum cmd_msg_state {tx_start,wait_cmd_out_and_ack,wait_ack,tx_timeout_fail,tx_kickout_fail,tx_done,tx_retransmit};
struct MCU_CTRL {unsigned int flags;int txq,ackq,tx_doneq;};
struct cmd_msg;
typedef struct adapter {
 struct MCU_CTRL MCUCtrl;unsigned int flags;
 struct {void (*andes_fill_cmd_header)(struct cmd_msg *,PNDIS_PACKET);
 int (*pci_kick_out_cmd_msg)(struct adapter *,struct cmd_msg *);} chipOps;
} *PRTMP_ADAPTER;
typedef struct adapter RTMP_ADAPTER;
struct cmd_msg {
 int need_wait,cmd_type,ext_cmd_type,timeout,need_retransmit,retransmit_times,ack_done;
 int wr_iot_checked,wr_iot_response_done,wr_iot_unsubmitted,wr_iot_firmware_result;
 enum cmd_msg_state state;
 unsigned int seq;PNDIS_PACKET net_pkt;
};
#define FALSE 0
#define TRUE 1
#define NDIS_STATUS_FAILURE 1
#define NDIS_STATUS_SUCCESS 0
#define EXT_CID 0xed
#define EXT_CMD_RADIO_ON_OFF_CTRL 5
#define RT_DEBUG_ERROR 0
#define RT_DEBUG_INFO 1
#define DBGPRINT(level,args) ((void)0)
#define MCU_INIT 0
#define OS_TEST_BIT(bit,p) ((void)(bit),*(p)&1u)
#define fRTMP_ADAPTER_MCU_SEND_IN_BAND_CMD 1u
#define fRTMP_ADAPTER_NIC_NOT_EXIST 2u
#define fRTMP_ADAPTER_SUSPEND 4u
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
#define RTMP_OS_EXIT_COMPLETION(p) ((void)(p))
#define RTMP_OS_INIT_COMPLETION(p) ((void)(p))
#define error_tx_timeout_fail 1
static struct cmd_msg *current;
static PRTMP_ADAPTER adapter;
static int mode,freed,force_frees,normal_frees,waits,unlinks,interrupt_context;
static int pending;
static int kick_for_precondition(PRTMP_ADAPTER ad,struct cmd_msg *msg){
 assert(ad==adapter&&msg==current&&!freed);
 msg->wr_iot_unsubmitted=TRUE;
 if(mode==3)return NDIS_STATUS_FAILURE;
 msg->wr_iot_unsubmitted=FALSE;
 msg->state=wait_ack;return NDIS_STATUS_SUCCESS;
}
#define AndesMTPciKickOutCmdMsg kick_for_precondition
static void complete(int *done){assert(!freed);(*done)++;}
#define RTMP_OS_COMPLETE complete
static int in_interrupt(void){return interrupt_context;}
static void AndesForceFreeCmdMsg(struct cmd_msg *msg){assert(msg==current&&!freed);freed=1;force_frees++;}
static void AndesFreeCmdMsg(struct cmd_msg *msg){assert(msg==current&&!freed);freed=1;normal_frees++;}
static void AndesQueueTailCmdMsg(int *queue,struct cmd_msg *msg,enum cmd_msg_state state){
 assert(msg==current&&!freed);msg->state=state;
 if(queue==&adapter->MCUCtrl.tx_doneq){freed=1;normal_frees++;}
 else {assert(queue==&adapter->MCUCtrl.txq);pending=1;}
}
static void AndesQueueHeadCmdMsg(int *queue,struct cmd_msg *msg,enum cmd_msg_state state){(void)queue;(void)msg;(void)state;assert(0);}
static int AndesDequeueAndKickOutCmdMsgs(PRTMP_ADAPTER ad){
 assert(ad==adapter&&!freed);current->state=wait_ack;
 if(mode==3||mode==5){current->wr_iot_unsubmitted=TRUE;current->state=tx_kickout_fail;RTMP_OS_COMPLETE(&current->ack_done);}
 return mode==3?1:0;
}
static int AndesWaitForCompleteTimeout(struct cmd_msg *msg,int timeout){
 assert(msg==current&&!freed&&!timeout);waits++;
 if(mode==1)return 0;
 if(mode==0||mode==4){msg->wr_iot_response_done=1;msg->wr_iot_firmware_result=0;}
 if(mode==4)msg->state=tx_kickout_fail;
 return 1;
}
static void AndesUnlinkCmdMsg(struct cmd_msg *msg,int *queue){assert(msg==current&&!freed&&queue==&adapter->MCUCtrl.ackq);unlinks++;}
static void AndesIncErrorCount(struct MCU_CTRL *ctl,int error){assert(ctl==&adapter->MCUCtrl&&error==1);}
'''
tail = r'''
int main(void){
 struct adapter ad;
 struct cmd_msg msg;int result;
 for(mode=0;mode<=5;mode++){
  memset(&ad,0,sizeof(ad));ad.flags=ad.MCUCtrl.flags=1;
  memset(&msg,0,sizeof(msg));msg.need_wait=msg.wr_iot_checked=1;
  msg.cmd_type=EXT_CID;msg.ext_cmd_type=5;msg.wr_iot_firmware_result=1;msg.retransmit_times=1;
  adapter=(PRTMP_ADAPTER)&ad;current=&msg;freed=force_frees=normal_frees=waits=unlinks=0;
  ad.chipOps.pci_kick_out_cmd_msg=kick_for_precondition;pending=0;
  result=AndesSendCmdMsg(adapter,&msg);
  assert(result==(mode==0?0:1)&&freed&&waits==1);
  assert(force_frees==((mode==3||mode==5)?1:0)&&normal_frees==((mode==3||mode==5)?0:1));
 }
 memset(&msg,0,sizeof(msg));msg.wr_iot_checked=1;current=&msg;freed=force_frees=normal_frees=waits=0;
 assert(AndesSendCmdMsg(adapter,&msg)==1&&force_frees==1&&!waits);
 interrupt_context=0;ad.chipOps.pci_kick_out_cmd_msg=NULL;
 memset(&msg,0,sizeof(msg));msg.need_wait=msg.wr_iot_checked=1;msg.cmd_type=EXT_CID;msg.ext_cmd_type=5;
 current=&msg;freed=force_frees=normal_frees=waits=0;
 assert(AndesSendCmdMsg(adapter,&msg)==1&&force_frees==1&&!waits);
 memset(&msg,0,sizeof(msg));msg.need_wait=msg.wr_iot_checked=1;msg.cmd_type=EXT_CID;msg.ext_cmd_type=5;
 current=&msg;freed=force_frees=normal_frees=waits=0;interrupt_context=1;
 assert(AndesSendCmdMsg(adapter,&msg)==1&&force_frees==1&&!waits);
 /* Checked commands must not enter legacy implicit retransmission. */
 interrupt_context=0;ad.chipOps.pci_kick_out_cmd_msg=kick_for_precondition;
 memset(&msg,0,sizeof(msg));msg.need_wait=msg.wr_iot_checked=msg.need_retransmit=1;
 msg.cmd_type=EXT_CID;msg.ext_cmd_type=5;msg.retransmit_times=3;
 current=&msg;freed=force_frees=normal_frees=waits=0;pending=0;
 assert(AndesSendCmdMsg(adapter,&msg)==1&&force_frees==1&&!waits&&!pending);
 puts("PASS extracted candidate sender: checked response, timeout, absent response, unsubmitted kickout, invalid state and preconditions; operations injected, no real concurrency proof");
 return 0;
}
'''
dispatch = ''
if a.with_dispatcher:
    fake_start = prefix.index('static int AndesDequeueAndKickOutCmdMsgs(')
    fake_end = prefix.index('\n}', fake_start) + 2
    prefix = prefix[:fake_start] + prefix[fake_end:]
    prefix += r'''
static struct cmd_msg *AndesDequeueCmdMsg(struct MCU_CTRL *ctl,int *queue){
 assert(ctl==&adapter->MCUCtrl&&queue==&ctl->txq);
 if(!pending)return NULL;
 pending=0;
 if(mode==5)adapter->flags=fRTMP_ADAPTER_NIC_NOT_EXIST;
 return current;
}
static unsigned int AndesGetCmdMsgSeq(PRTMP_ADAPTER ad){assert(ad==adapter);return 7;}
static void AndesBhSchedule(PRTMP_ADAPTER ad){assert(ad==adapter);}
'''
    start = source.index('static INT32 AndesDequeueAndKickOutCmdMsgs(')
    end = source.index('\n}', start) + 2
    dispatch = source[start:end]
a.output.write_text(prefix + dispatch + '\n' + sender + tail, encoding='utf-8')
