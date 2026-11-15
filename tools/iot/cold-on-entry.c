#define _GNU_SOURCE
#include <string.h>
#include <time.h>
#include "cold-on-entry.h"
#include "cold-on-select.h"
#include "cold-on-scheduler.h"
#include "rc-runtime.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
#include "control-record.h"
#include "physical-stop-wire.h"
#include "service-guard.h"
#include "precreated-entropy.h"
static void cold_entry_wipe(void *p,size_t n)
{volatile unsigned char *b=p;while(n--)*b++=0;}
enum wr_iot_radio_entry_result wr_iot_cold_on_entry(int radio_on,int reload)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_control_request request={0};struct wr_iot_physical_stop_request historical={0};
 struct wr_iot_down_result selected={0};struct timespec now;unsigned char bytes[32]={0};
 unsigned i;int guard,valid=0;enum wr_iot_cold_selection selection;
 enum wr_iot_radio_entry_result result=WR_RADIO_ENTRY_REFUSED;
 if(radio_on!=1)return WR_RADIO_ENTRY_NATIVE;
 if((reload!=0&&reload!=1)||wr_iot_cold_on_pending()||wr_iot_rc_shutdown.active||
    wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.radio_on_owned||
    wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_radio_off_receipt(&historical))return result;
 if(clock_gettime(CLOCK_MONOTONIC,&now)||now.tv_sec<=0||
    wr_iot_precreated_entropy(NULL,bytes,sizeof(bytes))!=(int)sizeof(bytes))goto done;
 selection=wr_iot_cold_select(bytes,&selected);
 if(selection==WR_COLD_SELECT_NATIVE){result=WR_RADIO_ENTRY_NATIVE;goto done;}
 if(selection!=WR_COLD_SELECT_ELIGIBLE)goto done;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)goto done;
 valid=wr_iot_rc_radio_on_saved_request(&request.request);
 wr_iot_service_guard_leave(guard);
 if(!valid||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned||
    wr_iot_rc_radio_off_receipt(&historical))goto done;
 for(i=0;i<16;i++){request.id[2*i]=hex[bytes[i]>>4];request.id[2*i+1]=hex[bytes[i]&15];}
 request.created=(unsigned long long)now.tv_sec;
 if(wr_iot_rc_cold_on_begin(&request,reload))result=WR_RADIO_ENTRY_OWNED;
 done:cold_entry_wipe(&request,sizeof(request));cold_entry_wipe(bytes,sizeof(bytes));return result;
}
