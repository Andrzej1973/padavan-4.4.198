#include "request.h"
#include <assert.h>
#include <stdio.h>
struct fixture {const char *enable,*ssid,*password,*gateway;char borrowed[128];};
static const char *read_value(void *context,const char *key){
 struct fixture *f=context;const char *value;
 if(!strcmp(key,"wr_iot_enable"))value=f->enable;
 else if(!strcmp(key,"wr_iot_ssid"))value=f->ssid;
 else if(!strcmp(key,"wr_iot_psk"))value=f->password;
 else if(!strcmp(key,"wr_iot_gateway"))value=f->gateway;
 else if(!strcmp(key,"wr_iot_mask"))value="255.255.255.0";
 else if(!strcmp(key,"wr_iot_start"))value="192.168.50.20";
 else {assert(!strcmp(key,"wr_iot_end"));value="192.168.50.200";}
 assert(strlen(value)<sizeof(f->borrowed));strcpy(f->borrowed,value);return f->borrowed;
}
int main(void){
 struct fixture f={"1","IoT test","password123","192.168.50.1",{0}};
 struct wr_iot_request out,before;struct wr_iot_range lan={0xc0a80100,0xc0a801ff};
 assert(wr_iot_request_read(&out,read_value,&f,1,1,0,&lan,1));
 assert(out.enabled&&!strcmp(out.ssid,"IoT test")&&!strcmp(out.password,"password123"));before=out;
#define BAD(router,radio,mode) do {assert(!wr_iot_request_read(&out,read_value,&f,router,radio,mode,&lan,1));assert(!memcmp(&out,&before,sizeof(out)));} while(0)
 BAD(0,1,0);BAD(1,0,0);BAD(1,1,1);BAD(1,1,2);BAD(1,1,3);
 f.enable="yes";BAD(1,1,0);f.enable="1";
 f.password="short";BAD(1,1,0);f.password="password123";
 f.ssid="bad\nSSID";BAD(1,1,0);f.ssid="IoT test";
 f.gateway="192.168.1.1";BAD(1,1,0);f.gateway="192.168.50.1";
 f.enable="0";assert(wr_iot_request_read(&out,read_value,&f,0,0,3,NULL,0));assert(!out.enabled&&!out.ssid[0]&&!out.password[0]);
 puts("PASS IoT request snapshot: borrowed values copied, credentials/subnet/modes validated, rejection preserves output; RC binding pending");return 0;
}
