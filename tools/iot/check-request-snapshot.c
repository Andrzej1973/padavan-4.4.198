#include "request-snapshot.h"
#include "request-stage.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

struct entry {const char *key;char value[128];};
static struct entry values[]={
 {"wr_iot_enable","1"},{"wr_iot_ssid","IoT test"},{"wr_iot_psk","password123"},
 {"wr_iot_gateway","192.168.50.1"},{"wr_iot_mask","255.255.255.0"},
 {"wr_iot_start","192.168.50.20"},{"wr_iot_end","192.168.50.200"},
 {"wr_iot_profile_t","0"},{"wr_iot_network_t","0"},{"wr_iot_firewall_t","0"},
 {"wr_iot_ssid_t","old SSID"},{"wr_iot_psk_t","old password"},
 {"wr_iot_gateway_t",""},{"wr_iot_mask_t",""},{"wr_iot_start_t",""},{"wr_iot_end_t",""}
};
static int depth,busy,writes,fail_write,silent_write;
static unsigned int bridge_index;
static struct entry *find(const char *key){size_t i;for(i=0;i<sizeof(values)/sizeof(values[0]);i++)if(!strcmp(values[i].key,key))return values+i;assert(0);return NULL;}
int wr_iot_service_guard_enter(int enabled){assert(enabled==1);if(!depth&&busy)return 0;depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth>0);depth--;}
unsigned int if_nametoindex(const char *name){assert(depth&&!strcmp(name,"br-iot"));return bridge_index;}
const char *nvram_safe_get(const char *key){assert(depth);return find(key)->value;}
int nvram_set_temp(const char *key,const char *value){assert(depth);writes++;if(writes==fail_write)return -1;if(writes==silent_write)return 0;assert(strlen(value)<sizeof(find(key)->value));strcpy(find(key)->value,value);return 0;}
int nvram_set_int_temp(const char *key,int value){char text[16];snprintf(text,sizeof(text),"%d",value);return nvram_set_temp(key,text);}
int wr_iot_network_check(const char *a,const char *b,const char *c,const char *d){assert(depth&&a&&b&&c&&d);return 1;}
static void reset(void){size_t i;assert(!depth);for(i=7;i<10;i++)strcpy(values[i].value,"0");strcpy(values[10].value,"old SSID");strcpy(values[11].value,"old password");for(i=12;i<16;i++)values[i].value[0]=0;writes=fail_write=silent_write=busy=0;bridge_index=0;}
static void prepared(struct wr_iot_request_snapshot *s){reset();memset(s,0,sizeof(*s));assert(wr_iot_request_snapshot_take(s)&&depth==1&&writes==0);assert(wr_iot_request_stage(1,1,0)&&depth==1);assert(!strcmp(find("wr_iot_profile_t")->value,"1"));writes=0;}
int main(void){
 struct wr_iot_request_snapshot s={0};int failure;
 prepared(&s);assert(wr_iot_request_snapshot_restore(&s)&&depth==1);
 assert(!strcmp(find("wr_iot_profile_t")->value,"0")&&!strcmp(find("wr_iot_psk_t")->value,"old password"));
 assert(wr_iot_request_snapshot_finish(&s)&&!depth&&!s.active&&!s.values[4][0]);
 for(failure=1;failure<=12;failure++){
  prepared(&s);fail_write=failure;
  assert(!wr_iot_request_snapshot_restore(&s)&&depth==1&&s.active);
  assert(!wr_iot_request_snapshot_finish(&s)&&depth==1);
  fail_write=0;writes=0;assert(wr_iot_request_snapshot_restore(&s));
  assert(wr_iot_request_snapshot_finish(&s)&&!depth);
 }
 prepared(&s);silent_write=5;
 assert(!wr_iot_request_snapshot_restore(&s)&&depth==1);
 silent_write=0;assert(wr_iot_request_snapshot_restore(&s));assert(wr_iot_request_snapshot_finish(&s));
 prepared(&s);bridge_index=7;
 assert(!wr_iot_request_snapshot_restore(&s)&&!writes&&depth==1);
 assert(!wr_iot_request_snapshot_finish(&s));
 bridge_index=0;assert(wr_iot_request_snapshot_restore(&s));assert(wr_iot_request_snapshot_finish(&s));
 reset();bridge_index=7;assert(!wr_iot_request_snapshot_take(&s)&&!depth&&!writes);
 reset();strcpy(find("wr_iot_firewall_t")->value,"1");assert(!wr_iot_request_snapshot_take(&s)&&!depth&&!writes);
 reset();memset(find("wr_iot_psk_t")->value,'x',80);find("wr_iot_psk_t")->value[80]=0;assert(!wr_iot_request_snapshot_take(&s)&&!depth&&!writes);
 reset();busy=1;assert(!wr_iot_request_snapshot_take(&s)&&!depth&&!writes);
 reset();assert(wr_iot_request_snapshot_take(&s));s.owner++;
 assert(!wr_iot_request_snapshot_restore(&s)&&!wr_iot_request_snapshot_finish(&s)&&!writes&&depth==1);
 s.owner=getpid();assert(wr_iot_request_snapshot_finish(&s)&&!depth);
 puts("PASS IoT temporary snapshot: nested stage retains outer guard, rollback/readback failures retain recovery, no bridge adoption; production startup not bound");return 0;
}
