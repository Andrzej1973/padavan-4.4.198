#!/usr/bin/env python3
"""Execute actual generated command-task attach and close bodies with OS faults."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
s=(a.candidate/'os/linux/rt_rbus_pci_drv.c').read_text()
def function(signature):
 i=s.index(signature);return s[i:s.index('\n}',i)+2]
functions='\n'.join(function(n) for n in ['NDIS_STATUS RtmpMgmtTaskInit(', 'INT wr_iot_command_task_exit_checked(', 'VOID RtmpMgmtTaskExit('])
prefix=r'''
#include <assert.h>
#include <string.h>
#include "terminal-command-owner.h"
#define MT7603 1
#define DMA_RESET_SUPPORT 1
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE -1
#define RTMP_TASK_STAT_STOPED 0
#define RTMP_TASK_STAT_UNKNOWN -1
#define DBGPRINT(a,b) ((void)0)
#define printk(...) ((void)0)
typedef int INT;typedef int NDIS_STATUS;typedef void VOID;typedef unsigned long ULONG;
typedef struct {int handle;} RTMP_OS_TASK;
typedef struct {int CmdQLock;struct {int CmdQState;} CmdQ;RTMP_OS_TASK cmdQTask;struct wr_iot_terminal_command_owner wr_iot_terminal_command;} RTMP_ADAPTER;
static int held,kills,attaches,fail_attach,retire_during_attach,kill_result;
static RTMP_ADAPTER *active;
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
#define RTMP_OS_TASK_LEGALITY(t) if ((t)->handle)
#define RTMP_OS_TASK_INIT(t,n,a) do{(void)(n);(void)(a);(t)->handle=0;}while(0)
static int RTPCICmdThread(void){return 0;}
static int wr_iot_os_join_context(void){assert(!held);return 0;}
static int wr_iot_os_command_task_current(RTMP_OS_TASK *t){assert(!held);return t->handle==1?0:-1;}
static int RtmpOSTaskAttach(RTMP_OS_TASK *t,int (*fn)(void),ULONG arg){
 (void)fn;(void)arg;assert(!held);attaches++;
 if(retire_during_attach){
  assert(active->wr_iot_terminal_command.attaching);
  assert(wr_iot_terminal_command_close(&active->wr_iot_terminal_command,1));
  assert(!wr_iot_terminal_command_join_begin(&active->wr_iot_terminal_command,1,1));
 }
 t->handle=fail_attach?-1:1;return fail_attach?-1:0;
}
static int RtmpOSTaskKill(RTMP_OS_TASK *t){assert(!held&&t->handle==1);kills++;return kill_result;}
#include "command-join-shared.inc"
#include "terminal-command-join.inc"
'''
tail=r'''
static void fresh(RTMP_ADAPTER *a){memset(a,0,sizeof(*a));wr_iot_terminal_command_init(&a->wr_iot_terminal_command,1);active=a;held=kills=attaches=fail_attach=retire_during_attach=kill_result=0;}
int main(void){RTMP_ADAPTER a;
 fresh(&a);assert(RtmpMgmtTaskInit(&a)==0&&attaches==1);
 assert(wr_iot_command_task_exit_checked(&a)==0&&kills==1);
 assert(RtmpMgmtTaskInit(&a)==0&&attaches==2&&!a.wr_iot_terminal_command.joined);
 RtmpMgmtTaskExit(&a);assert(kills==2);
 assert(wr_iot_terminal_command_close(&a.wr_iot_terminal_command,1));
 assert(wr_iot_terminal_command_join_checked(&a)==0&&kills==2);
 assert(RtmpMgmtTaskInit(&a)==-1&&attaches==2);
 fresh(&a);assert(RtmpMgmtTaskInit(&a)==0);kill_result=-1;
 assert(wr_iot_command_task_exit_checked(&a)==-1&&kills==1);
 assert(!a.wr_iot_terminal_command.joined);
 assert(RtmpMgmtTaskInit(&a)==-1&&attaches==1);
 kill_result=0;assert(wr_iot_command_task_exit_checked(&a)==0&&kills==2);
 fresh(&a);fail_attach=1;assert(RtmpMgmtTaskInit(&a)==-1);
 assert(wr_iot_terminal_command_close(&a.wr_iot_terminal_command,1));
 assert(wr_iot_terminal_command_join_checked(&a)==-1&&!kills);
 fresh(&a);retire_during_attach=1;assert(RtmpMgmtTaskInit(&a)==0);
 assert(wr_iot_terminal_command_join_checked(&a)==0&&kills==1);
 assert(!wr_iot_terminal_command_enqueue_allowed(&a.wr_iot_terminal_command));
 assert(!held);return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-command-calls-') as t:
 c=Path(t)/'check.c';exe=Path(t)/'check';c.write_text(prefix+functions+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-I'+str(Path(__file__).resolve().parent),str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS generated first attach, checked/legacy close, reopen, terminal receipt reuse, create failure and retirement during attach')
