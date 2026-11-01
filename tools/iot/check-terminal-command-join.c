#include <assert.h>
#include <string.h>
#include "terminal-command-owner.h"
typedef int INT;
typedef unsigned long ULONG;
typedef struct {
 int CmdQLock,cmdQTask;
 struct {int CmdQState;} CmdQ;
 struct wr_iot_terminal_command_owner wr_iot_terminal_command;
} RTMP_ADAPTER;
#define RTMP_TASK_STAT_STOPED 0
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE -1
static int held,bad_context,identity,kills,kill_result,reenter,identity_reads;
static RTMP_ADAPTER *active;
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static int wr_iot_os_join_context(void){assert(!held);return bad_context;}
static int wr_iot_os_command_task_current(int *t){(void)t;assert(!held);identity_reads++;return identity;}
INT wr_iot_terminal_command_join_checked(RTMP_ADAPTER *ad);
static int RtmpOSTaskKill(int *t){
 (void)t;assert(!held);kills++;
 if(reenter){reenter=0;assert(wr_iot_terminal_command_join_checked(active)==NDIS_STATUS_FAILURE);}
 return kill_result;
}
#include "terminal-command-join.inc"
#include "command-join-shared.inc"
static void reset(RTMP_ADAPTER *a){
 memset(a,0,sizeof(*a));wr_iot_terminal_command_init(&a->wr_iot_terminal_command,1);
 held=bad_context=identity=kills=identity_reads=reenter=0;kill_result=0;active=a;
}
int main(void){
 RTMP_ADAPTER a;int reads;
 reset(&a);assert(wr_iot_terminal_command_join_checked(0)==-1);
 assert(wr_iot_terminal_command_join_checked(&a)==-1&&!kills);
 assert(wr_iot_terminal_command_close(&a.wr_iot_terminal_command,1));
 bad_context=1;assert(wr_iot_terminal_command_join_checked(&a)==-1&&!kills);
 bad_context=0;identity=-1;assert(wr_iot_terminal_command_join_checked(&a)==-1&&!kills);
 identity=1;assert(wr_iot_terminal_command_join_checked(&a)==-1&&!kills);
 identity=0;kill_result=-1;
 assert(wr_iot_terminal_command_join_checked(&a)==-1&&kills==1);
 assert(!a.wr_iot_terminal_command.joined&&!a.wr_iot_terminal_command.joining);
 assert(!wr_iot_terminal_command_enqueue_allowed(&a.wr_iot_terminal_command));
 kill_result=0;reenter=1;
 assert(wr_iot_terminal_command_join_checked(&a)==0&&kills==2&&!held);
 reads=identity_reads;identity=-1;
 assert(wr_iot_terminal_command_join_checked(&a)==0&&kills==2&&identity_reads==reads);
 assert(!wr_iot_terminal_command_enqueue_allowed(&a.wr_iot_terminal_command));
 reset(&a);
 assert(wr_iot_command_first_attach_begin(&a.wr_iot_terminal_command,1)==1);
 assert(!wr_iot_command_normal_join_begin(&a.wr_iot_terminal_command,1,1));
 assert(wr_iot_command_attach_finish(&a.wr_iot_terminal_command,1,1));
 assert(wr_iot_command_join_shared_checked(&a)==0&&kills==1);
 assert(wr_iot_terminal_command_close(&a.wr_iot_terminal_command,1));
 identity=-1;
 assert(wr_iot_terminal_command_join_checked(&a)==0&&kills==1);
 assert(wr_iot_command_join_shared_checked(&a)==0&&kills==1);
 return 0;
}
