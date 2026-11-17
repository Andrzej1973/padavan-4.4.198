#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include "saved-config-store.h"
#include "generation-profile.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static char native_record[WR_IOT_SAVED_CONFIG_MAX],foreign[WR_IOT_SAVED_CONFIG_MAX];
static int present,read_error,writes,set_mode,reads;
static size_t fill_to;
static size_t filler(char *out,size_t used)
{
 unsigned slot=0;
 while(used<fill_to){
  char key[16];size_t remaining=fill_to-used,bytes=remaining>4096?4096:remaining;
  int n=snprintf(key,sizeof(key),"fill%u=",slot++);assert(n>0);
  if(remaining>bytes&&remaining-bytes<20)bytes-=20;
  assert(bytes>(size_t)n);memcpy(out+used,key,(size_t)n);
  memset(out+used+n,'x',bytes-(size_t)n-1);out[used+bytes-1]=0;used+=bytes;
 }
 return used;
}
int nvram_getall(char *out,int capacity,int temporary)
{
 int n;size_t used;
 assert(capacity==0x20000&&temporary==1);reads++;
 if(read_error){errno=ENOSPC;return -1;}
 memset(out,0,(size_t)capacity);
 n=snprintf(out,(size_t)capacity,"unrelated=preserve");assert(n>0);
 used=filler(out,(size_t)n+1);
 if(present){n=snprintf(out+used,(size_t)capacity-used,"%s=%s",WR_IOT_SAVED_CONFIG_KEY,native_record);assert(n>0);used+=(size_t)n+1;}
 if(used+1>61440){errno=ENOSPC;return -1;} /* Native NOR snapshot capacity. */
 return 0;
}
int nvram_set(const char *key,const char *value)
{
 assert(!strcmp(key,WR_IOT_SAVED_CONFIG_KEY));writes++;
 assert(writes==1); /* A single owner never retries SET. */
 if(set_mode==1)return -1;
 strcpy(native_record,set_mode==3?foreign:value);present=1;
 if(set_mode==4)read_error=1;
 return set_mode==2?-1:0;
}
static struct wr_iot_saved_config config={.profile={.enabled=0,.ssid="Configured IoT",
 .password="valid-password",.gateway="192.168.50.1",.mask="255.255.255.0",
 .first="192.168.50.20",.last="192.168.50.200"}};
static const char id[]="0123456789abcdef0123456789abcdef";
static void reset(void)
{
 assert(wr_iot_service_guard_dup()<0);
 memset(&wr_iot_rc_shutdown,0,sizeof(wr_iot_rc_shutdown));wr_iot_rc_shutdown.active=1;
 memset(native_record,0,sizeof(native_record));present=read_error=writes=set_mode=reads=0;
 fill_to=0;
}
static void empty(const struct wr_iot_saved_store *s)
{
 struct wr_iot_saved_store zero={0};assert(!memcmp(s,&zero,sizeof(*s)));
 assert(wr_iot_service_guard_dup()<0);
}
int main(void)
{
 struct wr_iot_saved_store s={0},copy;struct wr_iot_saved_config other=config;
 strcpy(other.profile.ssid,"Foreign IoT");assert(wr_iot_saved_config_encode(foreign,sizeof(foreign),&other));
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED != 1
 reset();assert(!wr_iot_saved_store_begin(&s,id,1,&config)&&!reads&&!writes);empty(&s);
 {
  struct wr_iot_saved_config captured=config;int found=17;
  struct wr_iot_generation_config pin={0};
  assert(wr_iot_service_guard_enter(1)==1);
  assert(!wr_iot_saved_config_capture(&captured,&found)&&found==17&&!reads&&!writes);
  assert(!memcmp(&captured,&config,sizeof(config)));
  assert(!wr_iot_generation_config_capture(&pin,id,1,&captured)&&!pin.owner&&!reads&&!writes);
  wr_iot_service_guard_leave(1);
 }
 puts("PASS unprepared saved store/capture refuse before native reads or writes");return 0;
#endif
 reset();wr_iot_rc_shutdown.active=0;assert(!wr_iot_saved_store_begin(&s,id,1,&config));
 wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=SIGTERM;
 assert(!wr_iot_saved_store_begin(&s,id,1,&config)&&!reads&&!writes);empty(&s);
 reset();read_error=1;assert(!wr_iot_saved_store_begin(&s,id,1,&config)&&!writes);empty(&s);
 reset();present=1;strcpy(native_record,"malformed");
 assert(!wr_iot_saved_store_begin(&s,id,1,&config)&&!writes);empty(&s);
 reset();assert(wr_iot_saved_store_begin(&s,id,1,&config)&&!writes);
 assert(!wr_iot_saved_store_begin(&s,id,1,&config));
 copy=s;assert(wr_iot_saved_store_step(&copy)==WR_IOT_SAVED_UNCERTAIN&&!writes);
 assert(!wr_iot_saved_store_finish(&copy)&&!wr_iot_saved_store_cancel(&copy));
 {pid_t child=fork();int status;assert(child>=0);
  if(!child){assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_UNCERTAIN&&!writes);_exit(0);}
  assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));}
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_RAM_READY&&writes==1);
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_RAM_READY&&writes==1);
 assert(!wr_iot_saved_store_cancel(&s));
 wr_iot_rc_shutdown.pending=SIGTERM;assert(wr_iot_saved_store_finish(&s));empty(&s);
 assert(wr_iot_rc_shutdown.pending==SIGTERM&&wr_iot_rc_shutdown.active==1);
 /* The same desired configuration needs no additional SET. */
 writes=0;wr_iot_rc_shutdown.pending=0;
 assert(wr_iot_saved_store_begin(&s,id,2,&config));
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_RAM_READY&&!writes);
 assert(wr_iot_saved_store_finish(&s));empty(&s);
 reset();assert(wr_iot_saved_store_begin(&s,id,3,&config));
 wr_iot_rc_shutdown.pending=SIGTERM;
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_UNCERTAIN&&!writes);
 assert(wr_iot_saved_store_cancel(&s));empty(&s);
 /* An uncertain SET that left the old record may be cancelled, not replayed. */
 reset();set_mode=1;assert(wr_iot_saved_store_begin(&s,id,4,&config));
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_UNCERTAIN&&writes==1);
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_UNCERTAIN&&writes==1);
 assert(!wr_iot_saved_store_finish(&s)&&wr_iot_saved_store_cancel(&s));empty(&s);
 /* A failed setter may have committed the one tuple; fresh read confirms RAM. */
 reset();set_mode=2;assert(wr_iot_saved_store_begin(&s,id,5,&config));
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_UNCERTAIN&&writes==1);
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_RAM_READY&&writes==1);
 assert(wr_iot_saved_store_finish(&s));empty(&s);
 reset();set_mode=4;assert(wr_iot_saved_store_begin(&s,id,6,&config));
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_UNCERTAIN&&writes==1);
 assert(!wr_iot_saved_store_finish(&s)&&!wr_iot_saved_store_cancel(&s));
 read_error=0;assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_RAM_READY&&writes==1);
 assert(wr_iot_saved_store_finish(&s));empty(&s);
 /* Foreign replacement retains the journal and never rolls back its data. */
 reset();assert(wr_iot_saved_store_begin(&s,id,7,&config));
 present=1;strcpy(native_record,foreign);
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_CONFLICT&&!writes);
 assert(!wr_iot_saved_store_cancel(&s)&&!wr_iot_saved_store_finish(&s));
 assert(!strcmp(native_record,foreign)&&s.owner==getpid());
 /* Explicit fixture-only restoration proves cancellation of the old baseline. */
 present=0;native_record[0]=0;assert(wr_iot_saved_store_cancel(&s));empty(&s);
 /* Preserve room for the native header/double NUL before attempting SET. */
 reset();fill_to=61440-20-2-16;
 assert(!wr_iot_saved_store_begin(&s,id,10,&config)&&!writes);empty(&s);
 reset();assert(wr_iot_saved_store_begin(&s,id,11,&config));fill_to=61440-20-2-16;
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_NO_SPACE&&!writes);
 assert(wr_iot_saved_store_cancel(&s));empty(&s);
 /* Replacing an existing tuple counts only its net growth, not two copies. */
 reset();present=1;strcpy(native_record,foreign);
 {char desired[WR_IOT_SAVED_CONFIG_MAX];size_t bytes;
  assert(wr_iot_saved_config_encode(desired,sizeof(desired),&config));
  bytes=strlen(WR_IOT_SAVED_CONFIG_KEY)+strlen(desired)+2;fill_to=61440-20-2-bytes;
  assert(wr_iot_saved_store_begin(&s,id,12,&config));
  assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_RAM_READY&&writes==1);
  assert(wr_iot_saved_store_finish(&s));empty(&s);
 }
 reset();present=1;strcpy(native_record,foreign);
 assert(wr_iot_saved_store_begin(&s,id,8,&config));
 assert(wr_iot_saved_store_cancel(&s)&&!writes&&!strcmp(native_record,foreign));empty(&s);
 reset();set_mode=3;assert(wr_iot_saved_store_begin(&s,id,9,&config));
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_CONFLICT&&writes==1);
 assert(wr_iot_saved_store_step(&s)==WR_IOT_SAVED_CONFLICT&&writes==1);
 assert(!wr_iot_saved_store_cancel(&s)&&!wr_iot_saved_store_finish(&s));
 assert(!strcmp(native_record,foreign));
 present=0;native_record[0]=0;assert(wr_iot_saved_store_cancel(&s));empty(&s);
 /* Cold provisioning needs a typed complete capture, not safe_get's
  * conflation of absence/read failure. It does not need runtime admission. */
 reset();
 {
  struct wr_iot_saved_config captured=config,before=config;int found=17;
  assert(!wr_iot_saved_config_capture(&captured,&found)&&found==17&&!reads&&!writes);
  assert(!memcmp(&captured,&before,sizeof(before)));
  assert(wr_iot_service_guard_enter(1)==1);wr_iot_rc_shutdown.active=0;
  assert(wr_iot_saved_config_capture(&captured,&found)&&!found&&!writes);
  assert(!memcmp(&captured,&before,sizeof(before)));
  read_error=1;found=17;
  assert(!wr_iot_saved_config_capture(&captured,&found)&&found==17);
  assert(!memcmp(&captured,&before,sizeof(before)));
  read_error=0;present=1;strcpy(native_record,"malformed");
  assert(!wr_iot_saved_config_capture(&captured,&found)&&found==17&&!writes);
  assert(!memcmp(&captured,&before,sizeof(before)));
  assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&config));
  memset(&captured,0,sizeof(captured));
  assert(wr_iot_saved_config_capture(&captured,&found)&&found==1&&!writes);
  assert(!captured.profile.enabled&&!strcmp(captured.profile.ssid,config.profile.ssid)&&
   !strcmp(captured.profile.password,config.profile.password)&&
   !strcmp(captured.profile.gateway,config.profile.gateway));
  assert(!wr_iot_saved_config_capture(NULL,&found)&&
         !wr_iot_saved_config_capture(&captured,NULL));
  wr_iot_saved_wipe(&captured,sizeof(captured));wr_iot_service_guard_leave(1);
 }
 /* Generation revision is PID/address/transaction bound and never follows
  * a desired change; absence also has to remain absent. Memory release does
  * not roll back native state and does not require a still-current revision. */
 reset();
 {
  struct wr_iot_generation_config pin={0},copied;
  struct wr_iot_saved_config captured=config;int status;pid_t child;
  assert(!wr_iot_generation_config_capture(&pin,id,11,&captured));
  assert(wr_iot_service_guard_enter(1)==1);
  assert(wr_iot_generation_config_capture(&pin,id,11,&captured)&&!pin.present);
  assert(wr_iot_generation_config_current(&pin,id,11)&&!writes);
  assert(!wr_iot_generation_config_current(&pin,id,12));
  copied=pin;assert(!wr_iot_generation_config_current(&copied,id,11)&&
                    !wr_iot_generation_config_release(&copied));
  child=fork();assert(child>=0);
  if(!child){assert(!wr_iot_generation_config_current(&pin,id,11)&&
                    !wr_iot_generation_config_release(&pin));_exit(0);}
  assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));
  present=1;assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&config));
  assert(!wr_iot_generation_config_current(&pin,id,11));
  assert(wr_iot_generation_config_release(&pin)&&!pin.owner&&!pin.record[0]);
  assert(wr_iot_generation_config_capture(&pin,id,12,&captured)&&pin.present);
  assert(wr_iot_generation_config_current(&pin,id,12));
  {
   struct wr_iot_precreated_profile_request selected={0};
   assert(wr_iot_generation_profile_enter(&pin));
   assert(!wr_iot_generation_profile_enter(&pin)&&!wr_iot_generation_config_release(&pin));
   assert(wr_iot_generation_profile_request(&selected)==1&&!strcmp(selected.ssid,config.profile.ssid));
   read_error=1;assert(wr_iot_generation_profile_request(&selected)==-1);read_error=0;
   assert(!wr_iot_generation_profile_leave(&copied));
   assert(wr_iot_generation_profile_leave(&pin));
   assert(wr_iot_generation_profile_request(&selected)==0);
   wr_iot_saved_wipe(&selected,sizeof(selected));
  }
  assert(!wr_iot_generation_config_capture(&pin,id,13,&captured));
  read_error=1;assert(!wr_iot_generation_config_current(&pin,id,12));read_error=0;
  strcpy(native_record,foreign);assert(!wr_iot_generation_config_current(&pin,id,12));
  assert(wr_iot_generation_config_release(&pin)&&!strcmp(native_record,foreign)&&!writes);
  wr_iot_service_guard_leave(1);
 }
 puts("PASS actual saved store + real service guard + existing snapshot parser: once-only native SET, unknown reads refuse, uncertain writes reobserve without replay, no-op/cancel/foreign retention, PID/address ownership; guarded typed desired capture and immutable generation revision, absence/error/change/PID/address/transaction refusal; NVRAM syscall model only, no flash/driver acceptance");
 return 0;
}
