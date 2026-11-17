#include <stdio.h> /* Vendor rc.h/shared declarations use FILE. */
#include <string.h>
#include <unistd.h>
#include "rc.h"
#include "control-record.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
#include "saved-config-store.h"
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
#include "wr-band-settings-snapshot.h"
#endif

/* Installation requires the existing Band Steering _nvram_getall ENOSPC
 * transform. An unpatched native dump can silently omit tuples and must not
 * certify absence. Use the existing owned, wiped snapshot implementation. */
static int read_record_budget(char record[WR_IOT_SAVED_CONFIG_MAX],int *present,
 const char *replacement,int *fits)
{
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 struct wr_band_settings_snapshot snapshot={0};
 struct wr_iot_saved_config checked={0};const char *value;int ok=0;
 size_t used=0,projected;
 if(WR_IOT_NATIVE_NVRAM_SPACE<=WR_IOT_NATIVE_NVRAM_HEADER_BYTES+2||
    WR_IOT_NATIVE_NVRAM_SPACE>0x20000)return 0;
 if(wr_band_snapshot_capture(&snapshot,0x20000,nvram_getall))return 0;
 value=wr_band_snapshot_get(&snapshot,WR_IOT_SAVED_CONFIG_KEY);
 if(!value){record[0]=0;*present=0;ok=1;goto budget;}
 if(!wr_iot_request_copy(record,WR_IOT_SAVED_CONFIG_MAX,value)||
    !wr_iot_saved_config_decode(&checked,record,strlen(record)))goto done;
 *present=1;ok=1;
 budget:
 if(replacement&&fits){
  while(used<snapshot.capacity&&snapshot.data[used])used+=strlen(snapshot.data+used)+1;
  projected=used;
  if(*present)projected-=strlen(WR_IOT_SAVED_CONFIG_KEY)+strlen(record)+2;
  projected+=strlen(WR_IOT_SAVED_CONFIG_KEY)+strlen(replacement)+2;
  *fits=projected<=(size_t)WR_IOT_NATIVE_NVRAM_SPACE-WR_IOT_NATIVE_NVRAM_HEADER_BYTES-2;
 }
 done:wr_band_snapshot_release(&snapshot);
 wr_iot_saved_wipe(&checked,sizeof(checked));return ok;
#else
 (void)record;(void)present;(void)replacement;(void)fits;return 0;
#endif
}
static int read_record(char record[WR_IOT_SAVED_CONFIG_MAX],int *present)
{return read_record_budget(record,present,NULL,NULL);}
static int admitted(void)
{
 return wr_iot_rc_shutdown.active==1&&!wr_iot_rc_shutdown.radio_on_owned&&
        !wr_iot_rc_shutdown.radio_off_owned;
}
static int owned(const struct wr_iot_saved_store *store)
{
 int fd;
 if(!store||store->owner!=getpid()||store->self!=(uintptr_t)store||
    store->token!=1||store->phase<WR_IOT_SAVED_PREPARED||
    store->phase>WR_IOT_SAVED_NO_SPACE||!store->created||
    !memchr(store->id,0,sizeof(store->id))||!wr_iot_control_id(store->id)||
    !memchr(store->prior,0,sizeof(store->prior))||
    !memchr(store->desired,0,sizeof(store->desired))||
    (store->prior_present!=0&&store->prior_present!=1)||
    (store->attempted!=0&&store->attempted!=1)||
    !admitted())return 0;
 fd=wr_iot_service_guard_dup();return fd>=0&&close(fd)==0;
}
static int same_prior(const struct wr_iot_saved_store *store,const char *record,int present)
{return present==store->prior_present&&!strcmp(store->prior,record);}
static void release(struct wr_iot_saved_store *store)
{
 int token=store->token;
 wr_iot_saved_wipe(store,sizeof(*store));wr_iot_service_guard_leave(token);
}
int wr_iot_saved_store_begin(struct wr_iot_saved_store *store,const char *id,
 unsigned long long created,const struct wr_iot_saved_config *config)
{
 struct wr_iot_saved_store candidate={0};int ok=0,fits=0;
 if(!store||store->owner||store->self||store->token||store->phase||
    !id||!wr_iot_control_id(id)||!created||!config||!admitted()||
    wr_iot_rc_shutdown.pending)return 0;
 if(!wr_iot_saved_config_encode(candidate.desired,sizeof(candidate.desired),config))goto done;
 candidate.token=wr_iot_service_guard_enter(1);if(candidate.token!=1)goto done;
 if(!admitted()||wr_iot_rc_shutdown.pending||
    !read_record_budget(candidate.prior,&candidate.prior_present,candidate.desired,&fits))goto done;
 if(!fits&&(!candidate.prior_present||strcmp(candidate.prior,candidate.desired)))goto done;
 candidate.owner=getpid();candidate.self=(uintptr_t)store;
 memcpy(candidate.id,id,sizeof(candidate.id));candidate.created=created;
 candidate.phase=WR_IOT_SAVED_PREPARED;*store=candidate;candidate.token=0;ok=1;
 done:if(candidate.token==1)wr_iot_service_guard_leave(candidate.token);
 wr_iot_saved_wipe(&candidate,sizeof(candidate));return ok;
}
enum wr_iot_saved_store_phase wr_iot_saved_store_step(struct wr_iot_saved_store *store)
{
 char record[WR_IOT_SAVED_CONFIG_MAX]={0};int present=0,result,fits=0;
 enum wr_iot_saved_store_phase phase=WR_IOT_SAVED_UNCERTAIN;
 if(!owned(store))return phase;
 if(!read_record_budget(record,&present,store->desired,&fits))goto done;
 if(store->phase==WR_IOT_SAVED_CONFLICT||store->phase==WR_IOT_SAVED_NO_SPACE){phase=store->phase;goto done;}
 if(store->attempted||store->phase==WR_IOT_SAVED_RAM_READY){
  if(present&&!strcmp(record,store->desired))store->phase=WR_IOT_SAVED_RAM_READY;
  else if(!same_prior(store,record,present))store->phase=WR_IOT_SAVED_CONFLICT;
  phase=store->phase;goto done;
 }
 if(!same_prior(store,record,present)){
  phase=store->phase=WR_IOT_SAVED_CONFLICT;goto done;
 }
 if(present&&!strcmp(record,store->desired)){
  phase=store->phase=WR_IOT_SAVED_RAM_READY;goto done;
 }
 if(!fits){phase=store->phase=WR_IOT_SAVED_NO_SPACE;goto done;}
 if(wr_iot_rc_shutdown.pending)goto done; /* No new SET during cancellation. */
 store->attempted=1;store->phase=WR_IOT_SAVED_UNCERTAIN;
 result=nvram_set(WR_IOT_SAVED_CONFIG_KEY,store->desired);
 /* SET is attempted once. An error can follow a completed mutation; later
  * steps only observe it and never replay SET or restore foreign data. */
 if(!read_record(record,&present))goto done;
 if(!present||strcmp(record,store->desired)){
  if(!same_prior(store,record,present))store->phase=WR_IOT_SAVED_CONFLICT;
 }else if(result==0)store->phase=WR_IOT_SAVED_RAM_READY;
 phase=store->phase;
 done:wr_iot_saved_wipe(record,sizeof(record));return phase;
}
static int end(struct wr_iot_saved_store *store,int cancel)
{
 char record[WR_IOT_SAVED_CONFIG_MAX]={0};int present=0,ok=0;
 if(!owned(store))return 0;
 if(!cancel&&store->phase!=WR_IOT_SAVED_RAM_READY)return 0;
 if(!read_record(record,&present))goto done;
 if(cancel?!same_prior(store,record,present):(!present||strcmp(record,store->desired)))goto done;
 release(store);ok=1;
 done:wr_iot_saved_wipe(record,sizeof(record));return ok;
}
int wr_iot_saved_store_finish(struct wr_iot_saved_store *store){return end(store,0);}
int wr_iot_saved_store_cancel(struct wr_iot_saved_store *store){return end(store,1);}
int wr_iot_saved_record_current(const char *expected)
{
 char record[WR_IOT_SAVED_CONFIG_MAX]={0};int present=0,fd,ok=0;
 if(!expected||!memchr(expected,0,WR_IOT_SAVED_CONFIG_MAX))return 0;
 fd=wr_iot_service_guard_dup();if(fd<0||close(fd))return 0;
 ok=read_record(record,&present)&&present&&!strcmp(record,expected);
 wr_iot_saved_wipe(record,sizeof(record));return ok;
}
