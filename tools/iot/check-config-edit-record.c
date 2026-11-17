#include "config-edit-record.h"
#include "control-record.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
 struct wr_iot_config_edit_record record={.id="0123456789abcdef0123456789abcdef",
 .revision="fedcba9876543210fedcba9876543210",.created=~0ULL,
 .fields={.profile={.enabled=0,.ssid="IoT \"<>\\: network",
 .gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}}};
 struct wr_iot_config_edit_record decoded,before;struct wr_iot_control_request legacy;
 char encoded[WR_IOT_CONTROL_RECORD_MAX],copy[WR_IOT_CONTROL_RECORD_MAX],small[2]={'x','y'};
 int mode,enabled,length;size_t index;
 for(mode=WR_IOT_EDIT_RAM;mode<=WR_IOT_EDIT_EXPLICIT;mode++)for(enabled=0;enabled<=1;enabled++){
  record.mode=mode;record.fields.profile.enabled=enabled;record.action=WR_IOT_CONFIG_KEY_KEEP;
  memset(record.fields.profile.password,0,sizeof(record.fields.profile.password));
  length=wr_iot_config_edit_record_encode(encoded,sizeof(encoded),&record);assert(length>0);
  assert(wr_iot_config_edit_record_decode(&decoded,encoded,(size_t)length));
  assert(decoded.mode==record.mode&&decoded.action==record.action&&decoded.created==record.created&&
         !strcmp(decoded.fields.profile.ssid,record.fields.profile.ssid)&&!decoded.fields.profile.password[0]);
  assert(wr_iot_control_decode(&legacy,encoded,(size_t)length));
  assert(legacy.operation==(enum wr_iot_operation)(WR_IOT_OPERATION_CONFIG_EDIT_RAM+mode)&&
         !strcmp(legacy.edit.revision,record.revision));
  record.action=WR_IOT_CONFIG_KEY_REPLACE;memset(record.fields.profile.password,'a',64);
  record.fields.profile.password[64]=0;
  length=wr_iot_config_edit_record_encode(encoded,sizeof(encoded),&record);assert(length>0&&length<512);
  assert(wr_iot_config_edit_record_decode(&decoded,encoded,(size_t)length));
  assert(!strcmp(decoded.fields.profile.password,record.fields.profile.password));
 }
 memset(&decoded,0x5a,sizeof(decoded));before=decoded;
 for(index=0;index<(size_t)length;index++){
  assert(!wr_iot_config_edit_record_decode(&decoded,encoded,index));
  assert(!memcmp(&decoded,&before,sizeof(decoded)));
 }
 memcpy(copy,encoded,(size_t)length);copy[0]='X';
 assert(!wr_iot_config_edit_record_decode(&decoded,copy,(size_t)length));
 assert(!memcmp(&decoded,&before,sizeof(decoded)));
 memcpy(copy,encoded,(size_t)length);copy[20]=0;
 assert(!wr_iot_config_edit_record_decode(&decoded,copy,(size_t)length));
 assert(!wr_iot_config_edit_record_encode(small,sizeof(small),&record)&&small[0]=='x'&&small[1]=='y');
 record.action=WR_IOT_CONFIG_KEY_KEEP;assert(!wr_iot_config_edit_record_encode(encoded,sizeof(encoded),&record));
 memset(record.fields.profile.password,0,sizeof(record.fields.profile.password));record.fields.profile.password[5]='x';
 assert(!wr_iot_config_edit_record_encode(encoded,sizeof(encoded),&record));
 memset(record.fields.profile.password,0,sizeof(record.fields.profile.password));record.mode=99;
 assert(!wr_iot_config_edit_record_encode(encoded,sizeof(encoded),&record));
 record.mode=WR_IOT_EDIT_EXPLICIT;record.action=WR_IOT_CONFIG_KEY_REPLACE;
 memset(record.fields.profile.ssid,'s',32);record.fields.profile.ssid[32]=0;
 memset(record.fields.profile.password,'a',64);record.fields.profile.password[64]=0;
 strcpy(record.fields.profile.gateway,"192.168.255.254");
 strcpy(record.fields.profile.mask,"255.255.255.128");
 strcpy(record.fields.profile.first,"192.168.255.129");
 strcpy(record.fields.profile.last,"192.168.255.253");
 length=wr_iot_config_edit_record_encode(encoded,sizeof(encoded),&record);
 assert(length>0&&length<=438&&wr_iot_config_edit_record_decode(&decoded,encoded,(size_t)length));
 puts("PASS bounded typed edit wire: explicit revision/mode/key intent, hex fields, KEEP no key, truncation/NUL/type refusal, envelope operation mapping; no RC edit execution");
 return 0;
}
