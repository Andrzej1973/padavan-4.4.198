#include "request-stage.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

struct entry {const char *key;char value[80];};
static int held,busy,enters,leaves;
static unsigned int bridge_index;
unsigned int if_nametoindex(const char *name){assert(held&&!strcmp(name,"br-iot"));return bridge_index;}
int wr_iot_service_guard_enter(int enabled){assert(enabled==1&&!held);enters++;if(busy)return 0;held=1;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&held);held=0;leaves++;}
static struct entry values[]={
 {"wr_iot_enable","1"},{"wr_iot_ssid","IoT test"},{"wr_iot_psk","password123"},
 {"wr_iot_gateway","192.168.50.1"},{"wr_iot_mask","255.255.255.0"},
 {"wr_iot_start","192.168.50.20"},{"wr_iot_end","192.168.50.200"},
 {"wr_iot_profile_t","stale"},{"wr_iot_network_t","stale"},{"wr_iot_firewall_t","stale"},
 {"wr_iot_gateway_t","stale"},{"wr_iot_mask_t","stale"},{"wr_iot_start_t","stale"},{"wr_iot_end_t","stale"}
};
static struct entry *find(const char *key){size_t i;for(i=0;i<sizeof(values)/sizeof(values[0]);i++)if(!strcmp(values[i].key,key))return &values[i];assert(0);return NULL;}
const char *nvram_safe_get(const char *key){assert(held);return find(key)->value;}
static int writes,fail_write;
int nvram_set_temp(const char *key,const char *value){assert(held);if(++writes==fail_write)return -1;assert(strlen(value)<sizeof(find(key)->value));strcpy(find(key)->value,value);return 0;}
int nvram_set_int_temp(const char *key,int value){assert(held);if(++writes==fail_write)return -1;assert(value==0||value==1);sprintf(find(key)->value,"%d",value);return 0;}
static void reset(void){strcpy(find("wr_iot_enable")->value,"1");strcpy(find("wr_iot_ssid")->value,"IoT test");strcpy(find("wr_iot_psk")->value,"password123");strcpy(find("wr_iot_gateway")->value,"192.168.50.1");strcpy(find("wr_iot_mask")->value,"255.255.255.0");strcpy(find("wr_iot_start")->value,"192.168.50.20");strcpy(find("wr_iot_end")->value,"192.168.50.200");strcpy(find("wr_iot_profile_t")->value,"stale");strcpy(find("wr_iot_network_t")->value,"stale");strcpy(find("wr_iot_firewall_t")->value,"stale");strcpy(find("wr_iot_gateway_t")->value,"stale");strcpy(find("wr_iot_mask_t")->value,"stale");strcpy(find("wr_iot_start_t")->value,"stale");strcpy(find("wr_iot_end_t")->value,"stale");}
int main(void){
 int failure;
 reset();assert(wr_iot_request_stage(1,1,0));assert(!strcmp(find("wr_iot_profile_t")->value,"1"));assert(!strcmp(find("wr_iot_network_t")->value,"0"));assert(!strcmp(find("wr_iot_firewall_t")->value,"0"));assert(!strcmp(find("wr_iot_gateway_t")->value,"192.168.50.1"));
 reset();strcpy(find("wr_iot_enable")->value,"0");assert(wr_iot_request_stage(0,0,3));assert(!strcmp(find("wr_iot_profile_t")->value,"0")&&!find("wr_iot_gateway_t")->value[0]);
 reset();strcpy(find("wr_iot_psk")->value,"short");assert(!wr_iot_request_stage(1,1,0));assert(!strcmp(find("wr_iot_profile_t")->value,"stale"));
 reset();assert(!wr_iot_request_stage(0,1,0));assert(!strcmp(find("wr_iot_profile_t")->value,"stale"));
 for(failure=1;failure<=12;failure++){
  reset();writes=0;fail_write=failure;
  assert(!wr_iot_request_stage(1,1,0));
  if(failure>=8)assert(!strcmp(find("wr_iot_profile_t")->value,"0")&&!strcmp(find("wr_iot_network_t")->value,"0")&&!strcmp(find("wr_iot_firewall_t")->value,"0"));
 }
 assert(!held&&enters==leaves);
 reset();writes=0;fail_write=0;bridge_index=7;
 assert(!wr_iot_request_stage(1,1,0)&&!writes&&!held);
 assert(!strcmp(find("wr_iot_profile_t")->value,"stale"));
 bridge_index=0;
 reset();writes=0;busy=1;
 assert(!wr_iot_request_stage(1,1,0)&&!writes&&!held&&enters==leaves+1);
 assert(!strcmp(find("wr_iot_profile_t")->value,"stale"));
 puts("PASS IoT request staging: service guard spans all reads/writes, busy lock preserves state, failure releases guard");return 0;
}
