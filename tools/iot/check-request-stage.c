#include "request-stage.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

struct entry {const char *key;char value[80];};
static int held,busy,enters,leaves;
static unsigned int bridge_index;
static int network_ok=1,network_checks;
int wr_iot_network_check(const char *gateway,const char *mask,const char *first,const char *last){assert(held);assert(!strcmp(gateway,"192.168.50.1")&&!strcmp(mask,"255.255.255.0")&&!strcmp(first,"192.168.50.20")&&!strcmp(last,"192.168.50.200"));network_checks++;return network_ok;}
unsigned int if_nametoindex(const char *name){assert(held&&!strcmp(name,"br-iot"));return bridge_index;}
int wr_iot_service_guard_enter(int enabled){assert(enabled==1&&!held);enters++;if(busy)return 0;held=1;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&held);held=0;leaves++;}
static struct entry values[]={
 {"wr_iot_request_enable","1"},{"wr_iot_request_ssid","IoT test"},{"wr_iot_request_psk","password123"},
 {"wr_iot_request_gateway","192.168.50.1"},{"wr_iot_request_mask","255.255.255.0"},
 {"wr_iot_request_start","192.168.50.20"},{"wr_iot_request_end","192.168.50.200"},
 {"wr_iot_profile_t","stale"},{"wr_iot_network_t","stale"},{"wr_iot_firewall_t","stale"},
 {"wr_iot_ssid_t","stale"},{"wr_iot_psk_t","stale"},
 {"wr_iot_gateway_t","stale"},{"wr_iot_mask_t","stale"},{"wr_iot_start_t","stale"},{"wr_iot_end_t","stale"},
 {"wr_iot_enable","0"},{"wr_iot_ssid","live SSID"},{"wr_iot_psk","live password"}
};
static struct entry *find(const char *key){size_t i;for(i=0;i<sizeof(values)/sizeof(values[0]);i++)if(!strcmp(values[i].key,key))return &values[i];assert(0);return NULL;}
const char *nvram_safe_get(const char *key){assert(held);return find(key)->value;}
static int writes,fail_write,drop_write;
int nvram_set_temp(const char *key,const char *value){assert(held);if(++writes==fail_write)return -1;if(writes==drop_write)return 0;assert(strlen(value)<sizeof(find(key)->value));strcpy(find(key)->value,value);return 0;}
int nvram_set_int_temp(const char *key,int value){assert(held);if(++writes==fail_write)return -1;assert(value==0||value==1);sprintf(find(key)->value,"%d",value);return 0;}
static void reset(void){strcpy(find("wr_iot_request_enable")->value,"1");strcpy(find("wr_iot_request_ssid")->value,"IoT test");strcpy(find("wr_iot_request_psk")->value,"password123");strcpy(find("wr_iot_request_gateway")->value,"192.168.50.1");strcpy(find("wr_iot_request_mask")->value,"255.255.255.0");strcpy(find("wr_iot_request_start")->value,"192.168.50.20");strcpy(find("wr_iot_request_end")->value,"192.168.50.200");strcpy(find("wr_iot_profile_t")->value,"0");strcpy(find("wr_iot_network_t")->value,"0");strcpy(find("wr_iot_firewall_t")->value,"0");strcpy(find("wr_iot_gateway_t")->value,"stale");strcpy(find("wr_iot_mask_t")->value,"stale");strcpy(find("wr_iot_start_t")->value,"stale");strcpy(find("wr_iot_end_t")->value,"stale");strcpy(find("wr_iot_enable")->value,"0");strcpy(find("wr_iot_ssid")->value,"live SSID");strcpy(find("wr_iot_psk")->value,"live password");}
static const char *direct_read(void *context,const char *key){
 assert(held&&context);
 if(!strcmp(key,"wr_iot_enable"))return "1";
 if(!strcmp(key,"wr_iot_ssid"))return context;
 if(!strcmp(key,"wr_iot_psk"))return "direct-password";
 if(!strcmp(key,"wr_iot_gateway"))return "192.168.50.1";
 if(!strcmp(key,"wr_iot_mask"))return "255.255.255.0";
 if(!strcmp(key,"wr_iot_start"))return "192.168.50.20";
 if(!strcmp(key,"wr_iot_end"))return "192.168.50.200";
 assert(0);return NULL;
}
int main(void){
 int failure;
 reset();writes=0;network_ok=0;
 assert(!wr_iot_request_stage(1,1,0)&&!writes&&!held&&network_checks==1);
 assert(!strcmp(find("wr_iot_profile_t")->value,"0"));
 strcpy(find("wr_iot_request_enable")->value,"0");
 assert(wr_iot_request_stage(0,0,3)&&network_checks==1);
 network_ok=1;
 reset();assert(wr_iot_request_stage(1,1,0));assert(!strcmp(find("wr_iot_profile_t")->value,"1"));assert(!strcmp(find("wr_iot_network_t")->value,"0"));assert(!strcmp(find("wr_iot_firewall_t")->value,"0"));assert(!strcmp(find("wr_iot_gateway_t")->value,"192.168.50.1"));assert(!strcmp(find("wr_iot_enable")->value,"0")&&!strcmp(find("wr_iot_ssid")->value,"live SSID")&&!strcmp(find("wr_iot_psk")->value,"live password"));
 reset();strcpy(find("wr_iot_request_enable")->value,"0");assert(wr_iot_request_stage(0,0,3));assert(!strcmp(find("wr_iot_profile_t")->value,"0")&&!find("wr_iot_gateway_t")->value[0]);
 reset();strcpy(find("wr_iot_request_psk")->value,"short");assert(!wr_iot_request_stage(1,1,0));assert(!strcmp(find("wr_iot_profile_t")->value,"0"));
 reset();assert(!wr_iot_request_stage(0,1,0));assert(!strcmp(find("wr_iot_profile_t")->value,"0"));
 reset();assert(wr_iot_request_stage(1,1,0));
 strcpy(find("wr_iot_request_psk")->value,"newpassword");
 assert(!strcmp(find("wr_iot_psk_t")->value,"password123"));
 for(failure=1;failure<=16;failure++){
  reset();writes=0;fail_write=failure;
  assert(!wr_iot_request_stage(1,1,0));
  if(failure>=10)assert(!strcmp(find("wr_iot_profile_t")->value,"0")&&!strcmp(find("wr_iot_network_t")->value,"0")&&!strcmp(find("wr_iot_firewall_t")->value,"0")&&!find("wr_iot_psk_t")->value[0]);
 }
 for(failure=4;failure<=9;failure++){
  reset();strcpy(find("wr_iot_ssid_t")->value,"stale");strcpy(find("wr_iot_psk_t")->value,"stale");
  strcpy(find("wr_iot_request_enable")->value,"0");writes=0;fail_write=0;drop_write=failure;
  assert(!wr_iot_request_stage(0,0,3)&&!held);
 }
 drop_write=0;
 assert(!held&&enters==leaves);
 reset();writes=0;fail_write=0;bridge_index=7;
 assert(!wr_iot_request_stage(1,1,0)&&!writes&&!held);
 assert(!strcmp(find("wr_iot_profile_t")->value,"0"));
 bridge_index=0;
 reset();writes=0;fail_write=0;
 assert(wr_iot_request_stage(1,1,0)&&!held);
 reset();writes=0;busy=1;
 assert(!wr_iot_request_stage(1,1,0)&&!writes&&!held&&enters==leaves+1);
 assert(!strcmp(find("wr_iot_profile_t")->value,"0"));
 busy=0;
 {
  static const char *gates[]={"wr_iot_profile_t","wr_iot_network_t","wr_iot_firewall_t"};
  size_t i;
  for(i=0;i<sizeof(gates)/sizeof(gates[0]);i++){
   reset();strcpy(find(gates[i])->value,"1");writes=0;
   assert(!wr_iot_request_stage(1,1,0)&&!writes&&!held);
   assert(!strcmp(find(gates[i])->value,"1"));
   reset();strcpy(find(gates[i])->value,"stale");writes=0;
   assert(!wr_iot_request_stage(1,1,0)&&!writes&&!held);
   assert(!strcmp(find(gates[i])->value,"stale"));
  }
 }
 reset();writes=0;fail_write=0;
 strcpy(find("wr_iot_request_enable")->value,"invalid");
 assert(wr_iot_request_stage_from(direct_read,"Direct IoT",1,1,0));
 assert(!strcmp(find("wr_iot_ssid_t")->value,"Direct IoT")&&
        !strcmp(find("wr_iot_psk_t")->value,"direct-password"));
 assert(!strcmp(find("wr_iot_request_enable")->value,"invalid")&&
        !strcmp(find("wr_iot_ssid")->value,"live SSID"));
 reset();writes=0;
 assert(!wr_iot_request_stage_from(direct_read,"",1,1,0)&&!writes&&!held);
 assert(!wr_iot_request_stage_from(NULL,NULL,1,1,0)&&!writes&&!held);
 busy=1;
 assert(!wr_iot_request_stage_from(direct_read,"Direct IoT",1,1,0)&&!writes&&!held);
 busy=0;network_ok=0;
 assert(!wr_iot_request_stage_from(direct_read,"Direct IoT",1,1,0)&&!writes&&!held);
 puts("PASS IoT request staging: candidate and direct input, guarded validation/writes, busy/invalid/overlap refusal");return 0;
}
