#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "generation-profile.h"
static int selection,legacy_reads,entropy_calls,malformed;
int wr_iot_generation_profile_request(struct wr_iot_precreated_profile_request *out)
{
 if(selection==1){memset(out,0,sizeof(*out));out->provisioned=1;
  strcpy(out->ssid,"Captured");strcpy(out->password,malformed?"short":"captured-password");}
 return selection;
}
static const char *legacy(void *unused,const char *key)
{
 (void)unused;legacy_reads++;
 if(!strcmp(key,"wr_iot_enable"))return "0";
 if(!strcmp(key,"wr_iot_ssid"))return "Legacy";
 assert(!strcmp(key,"wr_iot_psk"));return "legacy-password";
}
static int entropy(void *unused,unsigned char *bytes,unsigned length)
{(void)unused;(void)bytes;(void)length;entropy_calls++;return -1;}
int main(void)
{
 struct wr_iot_precreated_profile_request out,before;
 memset(&out,0x5a,sizeof(out));before=out;
 for(selection=-2;selection<=2;selection++){
  int result;legacy_reads=entropy_calls=0;out=before;
  result=wr_iot_generation_boot_request_read(&out,legacy,NULL,entropy,NULL);
  if(selection==1){assert(result&&out.provisioned&&!strcmp(out.ssid,"Captured")&&!legacy_reads&&!entropy_calls);}
  else if(selection==0){assert(result&&!strcmp(out.ssid,"Legacy")&&legacy_reads&&!entropy_calls);}
  else assert(!result&&!memcmp(&out,&before,sizeof(out))&&!legacy_reads&&!entropy_calls);
 }
 selection=1;malformed=1;out=before;legacy_reads=entropy_calls=0;
 assert(!wr_iot_generation_boot_request_read(&out,legacy,NULL,entropy,NULL)&&
  !memcmp(&out,&before,sizeof(out))&&!legacy_reads&&!entropy_calls);
 assert(!wr_iot_generation_boot_request_read(NULL,legacy,NULL,entropy,NULL));
 puts("PASS generation selector: captured view bypasses legacy/entropy; invalid bound view never falls back or changes output; unbound preserves legacy policy");
 return 0;
}
