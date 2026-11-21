#ifndef WR_IOT_CONFIG_EDIT_RECORD_H
#define WR_IOT_CONFIG_EDIT_RECORD_H
#include "control-record-common.h"
#include "config-edit.h"
enum wr_iot_config_edit_mode {WR_IOT_EDIT_RAM=0,WR_IOT_EDIT_AUTO=1,WR_IOT_EDIT_EXPLICIT=2,WR_IOT_EDIT_RUNTIME=3};
struct wr_iot_config_edit_record {
 char id[33],revision[33];unsigned long long created;
 enum wr_iot_config_edit_mode mode;
 enum wr_iot_config_key_action action;
 struct wr_iot_saved_config fields;
};
static inline int wr_iot_config_edit_record_valid(const struct wr_iot_config_edit_record *record)
{
 const struct wr_iot_request *profile;struct wr_iot_subnet subnet;size_t index;
 if(!record||!memchr(record->id,0,sizeof(record->id))||
    !memchr(record->revision,0,sizeof(record->revision))||
    !wr_iot_control_id(record->id)||!wr_iot_control_id(record->revision)||
    !record->created||record->mode<WR_IOT_EDIT_RAM||record->mode>WR_IOT_EDIT_RUNTIME||
    (record->mode==WR_IOT_EDIT_RUNTIME&&record->action!=WR_IOT_CONFIG_KEY_KEEP))return 0;
 profile=&record->fields.profile;
 if((profile->enabled!=0&&profile->enabled!=1)||
    !memchr(profile->ssid,0,sizeof(profile->ssid))||
    !memchr(profile->password,0,sizeof(profile->password))||
    !memchr(profile->gateway,0,sizeof(profile->gateway))||
    !memchr(profile->mask,0,sizeof(profile->mask))||
    !memchr(profile->first,0,sizeof(profile->first))||
    !memchr(profile->last,0,sizeof(profile->last))||
    !wr_shared_wifi_text(profile->ssid,1,32)||
    !wr_iot_subnet_plan(&subnet,profile->gateway,profile->mask,profile->first,profile->last,NULL,0))return 0;
 if(record->action==WR_IOT_CONFIG_KEY_REPLACE)return wr_shared_wifi_psk(profile->password);
 if(record->action!=WR_IOT_CONFIG_KEY_KEEP)return 0;
 for(index=0;index<sizeof(profile->password);index++)if(profile->password[index])return 0;
 return 1;
}
static inline int wr_iot_config_edit_record_decode(struct wr_iot_config_edit_record *out,
 const char *data,size_t length)
{
 char buffer[WR_IOT_CONTROL_RECORD_MAX]={0},*lines[13];
 struct wr_iot_config_edit_record candidate={0};size_t index,start=0,count=0,field,at;int ok=0;
 char *values[]={candidate.fields.profile.ssid,candidate.fields.profile.password,
  candidate.fields.profile.gateway,candidate.fields.profile.mask,
  candidate.fields.profile.first,candidate.fields.profile.last};
 const size_t capacities[]={33,65,16,16,16,16};
 if(!out||!data||!length||length>=sizeof(buffer)||memchr(data,0,length))goto done;
 memcpy(buffer,data,length);
 for(index=0;index<length;index++)if(buffer[index]=='\n'){
  if(count==13)goto done;
  lines[count++]=buffer+start;buffer[index]=0;start=index+1;
 }
 if(count!=13||start!=length||strcmp(lines[0],"WR-IOT-EDIT-1")||
    !wr_iot_control_id(lines[1])||!wr_iot_control_time(lines[2],&candidate.created)||
    !wr_iot_control_id(lines[3]))goto done;
 memcpy(candidate.id,lines[1],33);memcpy(candidate.revision,lines[3],33);
 if(!strcmp(lines[4],"ram"))candidate.mode=WR_IOT_EDIT_RAM;
 else if(!strcmp(lines[4],"auto"))candidate.mode=WR_IOT_EDIT_AUTO;
 else if(!strcmp(lines[4],"explicit"))candidate.mode=WR_IOT_EDIT_EXPLICIT;
 else if(!strcmp(lines[4],"runtime"))candidate.mode=WR_IOT_EDIT_RUNTIME;
 else goto done;
 if(!strcmp(lines[5],"keep"))candidate.action=WR_IOT_CONFIG_KEY_KEEP;
 else if(!strcmp(lines[5],"replace"))candidate.action=WR_IOT_CONFIG_KEY_REPLACE;
 else goto done;
 if(!strcmp(lines[6],"0"))candidate.fields.profile.enabled=0;
 else if(!strcmp(lines[6],"1"))candidate.fields.profile.enabled=1;
 else goto done;
 for(field=0;field<6;field++){
  size_t bytes=strlen(lines[field+7]);
  if(bytes%2||bytes/2>=capacities[field])goto done;
  for(at=0;at<bytes;at+=2){
   int high=wr_iot_saved_hex((unsigned char)lines[field+7][at]);
   int low=wr_iot_saved_hex((unsigned char)lines[field+7][at+1]);
   if(high<0||low<0||!(high||low))goto done;
   values[field][at/2]=(char)((high<<4)|low);
  }
 }
 if(!wr_iot_config_edit_record_valid(&candidate))goto done;
 *out=candidate;ok=1;
 done:wr_iot_saved_wipe(buffer,sizeof(buffer));
 wr_iot_saved_wipe(&candidate,sizeof(candidate));return ok;
}
static inline int wr_iot_config_edit_record_encode(char *out,size_t capacity,
 const struct wr_iot_config_edit_record *record)
{
 static const char hex[]="0123456789abcdef";
 char buffer[WR_IOT_CONTROL_RECORD_MAX]={0};
 struct wr_iot_config_edit_record checked={0};size_t used,field,index;int length=0,head;
 const char *values[6];
 if(!out||!wr_iot_config_edit_record_valid(record))goto done;
 values[0]=record->fields.profile.ssid;values[1]=record->fields.profile.password;
 values[2]=record->fields.profile.gateway;values[3]=record->fields.profile.mask;
 values[4]=record->fields.profile.first;values[5]=record->fields.profile.last;
 head=snprintf(buffer,sizeof(buffer),"WR-IOT-EDIT-1\n%s\n%llu\n%s\n%s\n%s\n%d\n",
  record->id,record->created,record->revision,
  record->mode==WR_IOT_EDIT_RAM?"ram":record->mode==WR_IOT_EDIT_AUTO?"auto":record->mode==WR_IOT_EDIT_EXPLICIT?"explicit":"runtime",
  record->action==WR_IOT_CONFIG_KEY_KEEP?"keep":"replace",record->fields.profile.enabled);
 if(head<=0||(size_t)head>=sizeof(buffer))goto done;
 used=(size_t)head;
 for(field=0;field<6;field++){
  for(index=0;values[field][index];index++){
   if(used+2>=sizeof(buffer))goto done;
   buffer[used++]=hex[(unsigned char)values[field][index]>>4];
   buffer[used++]=hex[(unsigned char)values[field][index]&15];
  }
  if(used+1>=sizeof(buffer))goto done;
  buffer[used++]='\n';
 }
 if(used+1>capacity||!wr_iot_config_edit_record_decode(&checked,buffer,used))goto done;
 memcpy(out,buffer,used+1);length=(int)used;
 done:wr_iot_saved_wipe(buffer,sizeof(buffer));
 wr_iot_saved_wipe(&checked,sizeof(checked));return length;
}
#endif
