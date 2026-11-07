#include "precreated-profile-request.h"
#include <assert.h>
#include <stdio.h>
struct fixture {const char *enable,*ssid,*password;char scratch[256];};
static const char *read_value(void *context,const char *key){
 struct fixture *f=context;const char *value=NULL;
 if(!strcmp(key,"wr_iot_enable"))value=f->enable;
 else if(!strcmp(key,"wr_iot_ssid"))value=f->ssid;
 else if(!strcmp(key,"wr_iot_psk"))value=f->password;
 assert(value);strcpy(f->scratch,value);return f->scratch;
}
int main(void){
 struct fixture f={"0","Reserved IoT","iot-password",{0}};
 struct wr_iot_precreated_profile_request out,before;
 for(unsigned n=0;n<3;n++){
  f.enable=(const char *[]){"0","1",""}[n];
  assert(wr_iot_precreated_profile_request_read(&out,read_value,&f));
  assert(out.requested_enabled==(n==1));
  assert(!strcmp(out.ssid,"Reserved IoT")&&!strcmp(out.password,"iot-password"));
 }
 memset(&out,0x5a,sizeof(out));before=out;f.enable="2";
 assert(!wr_iot_precreated_profile_request_read(&out,read_value,&f));assert(!memcmp(&out,&before,sizeof(out)));
 f.enable="0";f.password="short";
 assert(!wr_iot_precreated_profile_request_read(&out,read_value,&f));assert(!memcmp(&out,&before,sizeof(out)));
 f.password="iot-password";f.ssid="";
 assert(!wr_iot_precreated_profile_request_read(&out,read_value,&f));assert(!memcmp(&out,&before,sizeof(out)));
 /* Existing runtime OFF still needs no credentials or network parameters. */
 struct wr_iot_request runtime;f.enable="0";assert(wr_iot_request_read(&runtime,read_value,&f,1,1,0,NULL,0));
 assert(!runtime.enabled&&!runtime.ssid[0]&&!runtime.password[0]);
 puts("PASS cold request retains validated credentials while OFF/default-OFF; borrowed buffer snapshots and rejection atomicity; runtime OFF behavior unchanged. Empty unprovisioned credentials refuse; startup fallback not implemented.");return 0;
}
