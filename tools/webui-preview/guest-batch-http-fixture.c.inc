#include <fcntl.h>
typedef unsigned long long u64;
#define EVM_RESTART_WIFI2 1ULL
#define EVM_RESTART_WIFI5 2ULL
#define EVM_BLOCK_UNSAFE (1ULL<<63)
#define WIFI_GUEST_CONTROL_BIT 1
#define WIFI_COMMON_CHANGE_BIT 2
struct variable {const char *name;u64 event_mask;};
static struct variable http_tables[2][15];
static char http_names[2][14][64];
static int nvram_modified,rt_modified,wl_modified;
static u64 restart_needed_bits;
static int http_authorized=1,http_safe=1,http_open_fail,http_sink_fail,http_errno,http_readback_race;
static int http_opens,http_closes,http_calls,http_commits,http_notifications,http_manual,http_notified_flags;
static const char *GetServiceId(int sid){return sid==0?"WLANConfig11b":sid==1?"WLANConfig11a":NULL;}
static struct variable *GetVariables(int sid){assert(sid==0||sid==1);return http_tables[sid];}
static int get_login_safe(void){return http_safe;}
static int wr_modern_guest_post_allowed(void){return http_authorized;}
static const char *wr_shared_cgi_read(void *ctx,const char *key){return guest_cgi(ctx,key);}
static const char *wr_shared_nv_read(void *ctx,const char *key){return guest_nv(ctx,key);}
static const char *nvram_safe_get(const char *key){const char *v=_nvram_get(key);return v?v:"";}
static int nvram_get_int(const char *key){assert(!strcmp(key,"nvram_manual"));return http_manual;}
static int fixture_nvram_open(const char *path,int flags)
{assert(!strcmp(path,"/dev/nvram")&&flags==(O_RDWR|O_CLOEXEC));http_opens++;return http_open_fail?-1:7;}
static int fixture_nvram_close(int fd){assert(fd==7);http_closes++;return 0;}
static FILE *fixture_batch_sink(const char *path,const char *mode){return http_sink_fail?NULL:fopen(path,mode);}
static int asus_nvram_commit(int id,FILE *sink,int argc,char **argv)
{(void)id;(void)sink;(void)argc;(void)argv;if(nvram_modified&&!http_manual)http_commits++;nvram_modified=0;return 0;}
static int ej_notify_services(int id,FILE *sink,int argc,char **argv)
{(void)id;(void)sink;(void)argc;(void)argv;if(restart_needed_bits){http_notifications++;http_notified_flags=rt_modified|wl_modified;}restart_needed_bits=0;rt_modified=wl_modified=0;return 0;}
static int http_batch_ioctl(const void *request)
{
 http_calls++;if(http_errno){errno=http_errno;return -1;}
 long result=dev_nvram_ioctl(NULL,WR_NVRAM_IOCTL_BATCH_V1,(unsigned long)request);
 if(result<0){errno=(int)-result;return -1;}
 if(http_readback_race){depth=1;assert(!_nvram_set("rt_guest_ssid","raced-after-batch",0));depth=0;}
 return (int)result;
}
/* HTTP_HANDLER */
static void reset_http_batch(void)
{
 reset_store();http_ioctl_mode=1;http_authorized=http_safe=1;
 http_open_fail=http_sink_fail=http_errno=http_readback_race=0;
 http_opens=http_closes=http_calls=http_commits=http_notifications=http_manual=http_notified_flags=0;
 nvram_modified=rt_modified=wl_modified=0;restart_needed_bits=0;
 guest_band="rt";guest_intent="keep";guest_open=0;guest_values[13]=NULL;
 depth=1;
 for(unsigned int band=0;band<2;band++)for(unsigned int i=0;i<14;i++){
  snprintf(http_names[band][i],64,"%s_guest_%s",band?"wl":"rt",wr_modern_guest_fields[i]);
  http_tables[band][i]=(struct variable){http_names[band][i],band?EVM_RESTART_WIFI5:EVM_RESTART_WIFI2};
  assert(!_nvram_set(http_names[band][i],i==13?"stored-guest-key":guest_old[i],0));
  if(i<13)guest_values[i]=guest_old[i];
 }depth=0;guest_values[1]="NewGuest";
}
static void check_http_batch(const char *state,int may_change)
{
 char *json=NULL;size_t size=0;FILE *stream=open_memstream(&json,&size);assert(stream);
 do_wr_modern_guest_apply("wr_modern_guest_apply.json",stream);assert(!fclose(stream));
 char expected[128];snprintf(expected,sizeof(expected),"\"state\":\"%s\"",state);assert(strstr(json,expected));
 snprintf(expected,sizeof(expected),"\"settingsMayHaveChanged\":%s",may_change?"true":"false");assert(strstr(json,expected));
 assert(strstr(json,"\"runtimeVerified\":false")&&strstr(json,"\"automaticRetry\":false"));
 assert(!strstr(json,"stored-guest-key")&&!strstr(json,"NewGuest"));
 printf("BATCH_HTTP_REPLY %s",json);free(json);
}
static void guest_batch_http_cases(void)
{
 reset_http_batch();check_http_batch("configuration_matches",1);
 assert(http_calls==1&&http_closes==1&&http_commits==1&&http_notifications==1&&http_notified_flags==WIFI_COMMON_CHANGE_BIT);
 check_http_batch("reload_required",0);assert(http_calls==1&&http_commits==1);
 reset_http_batch();guest_values[1]=guest_old[1];guest_values[0]="0";
 check_http_batch("configuration_matches",1);assert(http_notified_flags==WIFI_GUEST_CONTROL_BIT);
 reset_http_batch();guest_values[1]=guest_old[1];check_http_batch("configuration_matches",0);assert(http_calls==1&&!http_commits&&!http_notifications);
 reset_http_batch();http_manual=1;check_http_batch("configuration_matches",1);assert(!http_commits&&http_notifications==1);
 for(int mode=0;mode<3;mode++){
  reset_http_batch();guest_band="wl";
  if(mode==1){guest_intent="change";guest_values[13]="replacement-key";}
  if(mode==2){guest_open=1;guest_values[3]="open";}
  check_http_batch("configuration_matches",1);
  assert(http_calls==1&&http_commits==1&&http_notifications==1&&http_notified_flags==WIFI_COMMON_CHANGE_BIT);
  assert(!strcmp(_nvram_get("rt_guest_ssid"),"Guest")&&!strcmp(_nvram_get("wl_guest_ssid"),"NewGuest"));
  assert(!strcmp(_nvram_get("wl_guest_wpa_psk"),mode==1?"replacement-key":"stored-guest-key"));
 }
 int errors[]={EINVAL,ENOTTY,EPERM,ENOMEM,ENOSPC,EFAULT,EAGAIN,EINTR,EIO};
 for(unsigned int i=0;i<ARRAYSIZE(errors);i++){
  reset_http_batch();http_errno=errors[i];
  check_http_batch(errors[i]==EAGAIN?"reload_required":(errors[i]==EINTR||errors[i]==EIO)?"unconfirmed":"unavailable",errors[i]==EINTR||errors[i]==EIO);
  assert(http_calls==1&&http_closes==1&&!http_commits&&!http_notifications);
  assert(!strcmp(_nvram_get("rt_guest_ssid"),"Guest"));
 }
 reset_http_batch();http_readback_race=1;check_http_batch("unconfirmed",1);assert(!http_commits&&!http_notifications&&!restart_needed_bits&&!nvram_modified);
 reset_http_batch();http_open_fail=1;check_http_batch("unavailable",0);assert(!http_calls&&!http_closes);
 reset_http_batch();http_sink_fail=1;check_http_batch("unavailable",0);assert(!http_calls&&!http_opens);
 reset_http_batch();http_authorized=0;check_http_batch("rejected",0);assert(!http_calls&&!http_opens);
 reset_http_batch();nvram_modified=1;check_http_batch("busy",0);assert(!http_calls&&!http_opens);
 reset_http_batch();http_safe=0;http_tables[0][1].event_mask|=EVM_BLOCK_UNSAFE;
 check_http_batch("rejected",0);assert(!http_calls&&!http_opens);
 http_ioctl_mode=0;
 puts("PASS actual candidate HTTP batch handler + actual ioctl/core: one call, no partial fallback, no-op/replay/manual, control/common notification, errno/uncertain/readback/auth/busy/unsafe/open/sink gates; commit/RC substituted");
}
