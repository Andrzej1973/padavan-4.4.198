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
#include "rc-runtime.h"
#include "radio-on-owner.h"
#include "cold-on-entry.h"
static void entry_wipe(void*p,size_t n)
{volatile unsigned char*b=p;while(n--)*b++=0;}
enum wr_iot_radio_entry_result wr_iot_restart_entry(int radio_on,int reload)
{
 struct wr_iot_control_request off={0};struct wr_iot_rc_mode a={0},b={0};
 struct wr_iot_rc_physical_intent intent={1,1,0};struct timespec now;
 unsigned char bytes[32]={0};unsigned i,nonzero=0;int guard,valid=0;enum wr_iot_radio_entry_result result=WR_RADIO_ENTRY_REFUSED;
 static const char hex[]="0123456789abcdef";
 if(radio_on!=1||!wr_iot_rc_restart_owned())return WR_RADIO_ENTRY_NATIVE;
 if((reload!=0&&reload!=1)||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return WR_RADIO_ENTRY_REFUSED;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return WR_RADIO_ENTRY_REFUSED;
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
  result=wr_iot_rc_physical_begin_quiesce(&intent,&off)?WR_RADIO_ENTRY_OWNED:WR_RADIO_ENTRY_REFUSED;
 entry_wipe(bytes,sizeof(bytes));entry_wipe(&off,sizeof(off));return result;
}

enum wr_iot_radio_entry_result wr_iot_radio_on_entry(int radio_on,int reload)
{
 struct wr_iot_physical_stop_request receipt={0},after={0};
 struct wr_iot_control_request request={0};struct timespec now;
 unsigned char bytes[32]={0},a[64],b[64];unsigned i,nonzero=0;
 int guard,valid=0;enum wr_iot_radio_entry_result result=WR_RADIO_ENTRY_REFUSED;
 static const char hex[]="0123456789abcdef";
 if(radio_on!=1)return WR_RADIO_ENTRY_NATIVE;
 if((reload!=0&&reload!=1)||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return result;
 if(!wr_iot_rc_radio_off_receipt(&receipt))return wr_iot_cold_on_entry(radio_on,reload);
 if(receipt.action!=WR_STOP_RELEASE||!wr_iot_physical_stop_request_valid(&receipt))return result;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return result;
 if(wr_iot_rc_radio_on_saved_request(&request.request)&&
    clock_gettime(CLOCK_MONOTONIC,&now)==0&&now.tv_sec>0&&
    wr_iot_precreated_entropy(NULL,bytes,sizeof(bytes))==(int)sizeof(bytes)&&
    wr_iot_rc_radio_off_receipt(&after)&&
    wr_iot_physical_stop_request_encode(a,sizeof(a),&receipt)&&
    wr_iot_physical_stop_request_encode(b,sizeof(b),&after)&&!memcmp(a,b,sizeof(a))){
  for(i=0;i<16;i++){nonzero|=bytes[i];request.id[2*i]=hex[bytes[i]>>4];request.id[2*i+1]=hex[bytes[i]&15];}
  request.created=(unsigned long long)now.tv_sec;valid=nonzero!=0;
 }
 wr_iot_service_guard_leave(guard);
 if(valid&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
    wr_iot_rc_radio_on_begin(&request,reload))result=WR_RADIO_ENTRY_OWNED;
 entry_wipe(bytes,sizeof(bytes));entry_wipe(&request,sizeof(request));return result;
}

enum wr_iot_radio_entry_result wr_iot_radio_off_entry(int radio_on,int reload)
{
 struct wr_iot_control_request request={0};struct wr_iot_physical_stop_request receipt={0};
 struct wr_iot_rc_mode a={0},b={0};struct timespec now;
 unsigned char bytes[32]={0};unsigned i,nonzero=0;int guard,valid=0;
 enum wr_iot_radio_entry_result result=WR_RADIO_ENTRY_REFUSED;
 static const char hex[]="0123456789abcdef";
 if(radio_on!=0)return WR_RADIO_ENTRY_NATIVE;
 if((reload!=0&&reload!=1)||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return result;
 /* An existing receipt is preserved, never replaced by a second OFF. */
 if(wr_iot_rc_radio_off_receipt(&receipt))return result;
 if(!wr_iot_rc_restart_owned())return WR_RADIO_ENTRY_NATIVE;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return result;
 if(wr_iot_rc_mode_read(&a)&&a.router==1&&a.mode==0&&
    clock_gettime(CLOCK_MONOTONIC,&now)==0&&now.tv_sec>0&&
    wr_iot_precreated_entropy(NULL,bytes,sizeof(bytes))==(int)sizeof(bytes)&&
    wr_iot_rc_mode_read(&b)&&a.router==b.router&&a.radio==b.radio&&a.mode==b.mode&&
    wr_iot_rc_restart_owned()){
  for(i=0;i<16;i++){nonzero|=bytes[i];request.id[2*i]=hex[bytes[i]>>4];request.id[2*i+1]=hex[bytes[i]&15];}
  request.created=(unsigned long long)now.tv_sec;valid=nonzero!=0;
 }
 wr_iot_service_guard_leave(guard);
 if(valid&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
    wr_iot_rc_radio_off_begin(&request,reload))result=WR_RADIO_ENTRY_OWNED;
 entry_wipe(bytes,sizeof(bytes));entry_wipe(&request,sizeof(request));return result;
}
