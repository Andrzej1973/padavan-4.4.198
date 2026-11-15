#define _GNU_SOURCE
#include <time.h>
#include <string.h>
#include "restart-entry.h"
#include "rc-backend.h"
#include "rc-physical-stop.h"
#include "control-record.h"
#include "service-guard.h"
#include "precreated-entropy.h"
#include "rc-shutdown-admission.h"
static void entry_wipe(void*p,size_t n)
{volatile unsigned char*b=p;while(n--)*b++=0;}
int wr_iot_restart_entry(int radio_on,int reload)
{
 struct wr_iot_control_request off={0};struct wr_iot_rc_mode a={0},b={0};
 struct wr_iot_rc_physical_intent intent={1,1,0};struct timespec now;
 unsigned char bytes[32]={0};unsigned i,nonzero=0;int guard,valid=0,result=0;
 static const char hex[]="0123456789abcdef";
 if(!wr_iot_rc_restart_owned())return 0;
 if(radio_on!=1||(reload!=0&&reload!=1)||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(!wr_iot_rc_mode_read(&a)||a.router!=1||a.radio!=1||a.mode!=0||
    clock_gettime(CLOCK_MONOTONIC,&now)||now.tv_sec<=0||
    wr_iot_precreated_entropy(NULL,bytes,sizeof(bytes))!=(int)sizeof(bytes))goto release;
 for(i=0;i<16;i++)nonzero|=bytes[i];
 if(!nonzero)goto release;
 if(!wr_iot_rc_mode_read(&b)||a.router!=b.router||a.radio!=b.radio||a.mode!=b.mode)goto release;
 for(i=0;i<16;i++){off.id[2*i]=hex[bytes[i]>>4];off.id[2*i+1]=hex[bytes[i]&15];}
 off.created=(unsigned long long)now.tv_sec;intent.reload=(unsigned)reload;valid=1;
 release:wr_iot_service_guard_leave(guard);
 /* Physical controller must acquire its own outer admission/guard. Never
  * hold a borrowed guard across its fence or copy a live physical context. */
 if(valid&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending)
  result=wr_iot_rc_physical_begin_quiesce(&intent,&off);
 entry_wipe(bytes,sizeof(bytes));entry_wipe(&off,sizeof(off));return result;
}
