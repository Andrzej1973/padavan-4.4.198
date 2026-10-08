/* Candidate profile transformation; lifecycle/network integration is separate. */
#ifndef WR_IOT_PROFILE_LINE_H
#define WR_IOT_PROFILE_LINE_H
#include "profile-list.h"
#include "../shared-wifi/validate.h"
static int wr_iot_profile_line(char *out,size_t capacity,const char *line,const char *ssid,const char *password,int enabled) {
 static const struct {const char *key,*third;} lists[]={
  {"AuthMode","WPA2PSK"},{"EncrypType","AES"},{"WmmCapable","1"},
  {"DLSCapable","0"},{"NoForwarding","1"},{"HideSSID","0"},
  {"StationKeepAlive","0"},{"PreAuth","0"},{"IEEE8021X","0"},
  {"FixedTxMode","0"},{"HT_MCS","33"}
 };
 const char *eq,*replacement=NULL;size_t length,key_size,i,value_size,total;int newline;
 char value[1024],extended[1200];
 struct wr_shared_wifi_fields credentials={ssid,"psk","0","2","aes",password};
 if(!out||!line)return 0;
 length=strlen(line);
 if(!enabled){if(length>=capacity)return 0;memmove(out,line,length+1);return 1;}
 if(wr_shared_wifi_validate(&credentials)!=WR_SHARED_WIFI_OK)return 0;
 eq=strchr(line,'=');
 if(!eq){if(length>=capacity)return 0;memmove(out,line,length+1);return 1;}
 key_size=(size_t)(eq-line);newline=length&&line[length-1]=='\n';
 value_size=length-key_size-1-(size_t)newline;
 if(key_size==8&&!strncmp(line,"BssidNum",8)){
  if(value_size!=1||eq[1]!='2')return 0;
  replacement="3";
 }else if(key_size==5&&!strncmp(line,"SSID3",5))replacement=ssid;
 else if(key_size==7&&!strncmp(line,"WPAPSK3",7))replacement=password;
 else {
  for(i=0;i<sizeof(lists)/sizeof(lists[0]);i++)if(strlen(lists[i].key)==key_size&&!strncmp(line,lists[i].key,key_size)){
   if(value_size>=sizeof(value))return 0;
   memcpy(value,eq+1,value_size);value[value_size]='\0';
   if(!wr_iot_profile_list(extended,sizeof(extended),value,lists[i].third,1))return 0;
   replacement=extended;break;
  }
 }
 if(!replacement){if(length>=capacity)return 0;memmove(out,line,length+1);return 1;}
 total=key_size+1+strlen(replacement)+(size_t)newline;
 if(total>=capacity)return 0;
 memmove(out,line,key_size+1);memcpy(out+key_size+1,replacement,strlen(replacement));
 if(newline)out[total-1]='\n';
 out[total]='\0';return 1;
}
#endif
