#define main old_cold_request_fixture
#include "check-precreated-profile-request.c"
#undef main
static unsigned calls;static int mode;
static int entropy(void *context,unsigned char *bytes,unsigned int length){
 (void)context;calls++;assert(length==32);
 for(unsigned i=0;i<length;i++)bytes[i]=mode==2?0:(unsigned char)(i+1);
 return mode==1?31:mode==3?-1:32;
}
int main(void){
 struct fixture f={"0","","",{0}};struct wr_iot_precreated_profile_request out,before;
 memset(&out,0x5a,sizeof(out));before=out;
 for(mode=1;mode<=3;mode++){
  assert(!wr_iot_precreated_boot_request_read(&out,read_value,&f,entropy,NULL));
  assert(!memcmp(&out,&before,sizeof(out)));
 }
 mode=0;assert(wr_iot_precreated_boot_request_read(&out,read_value,&f,entropy,NULL));
 assert(!out.provisioned&&!out.requested_enabled&&strlen(out.password)==64);
 assert(!strcmp(out.ssid,"WR1200JS-IoT"));
 assert(!strcmp(f.ssid,"")&&!strcmp(f.password,""));
 assert(!wr_iot_precreated_profile_request_read(&out,read_value,&f));
 unsigned previous=calls;f.ssid="Configured";
 assert(!wr_iot_precreated_boot_request_read(&out,read_value,&f,entropy,NULL)&&calls==previous);
 f.password="valid-password";assert(wr_iot_precreated_boot_request_read(&out,read_value,&f,entropy,NULL));
 assert(out.provisioned&&!out.requested_enabled&&!strcmp(out.password,f.password)&&calls==previous);
 f.enable="1";f.ssid=f.password="";
 assert(!wr_iot_precreated_boot_request_read(&out,read_value,&f,entropy,NULL)&&calls==previous);
 puts("PASS factory cold reservation policy: entropy error/short/allzero refuse; ephemeral key only for wholly empty OFF config; saved requests untouched; invalid/ON inputs never substituted. Injected entropy, not production CSPRNG readiness proof.");return 0;
}
