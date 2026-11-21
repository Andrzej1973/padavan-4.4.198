#ifndef WR_IOT_CONFIG_VIEW_JSON_H
#define WR_IOT_CONFIG_VIEW_JSON_H
#include "config-view.h"
#include "control-record-common.h"
#define WR_IOT_VIEW_JSON_MAX 768
static inline int wr_iot_config_view_json(char *out,size_t capacity,
 const struct wr_iot_config_view *view,const char revision[33])
{
 static const char hex[]="0123456789abcdef";
 char buffer[WR_IOT_VIEW_JSON_MAX]={0},ssid[193]={0};size_t index,used=0;int length=0,written;
 if(!out||!view||!revision||!memchr(revision,0,33)||
    !wr_iot_control_id(revision)||!wr_iot_config_view_valid(view))goto done;
 for(index=0;view->ssid[index];index++){
  unsigned char value=(unsigned char)view->ssid[index];
  if(value=='"'||value=='\\'){ssid[used++]='\\';ssid[used++]=(char)value;}
  else if(value<0x20||value=='<'||value=='>'||value=='&'){
   memcpy(ssid+used,"\\u00",4);used+=4;ssid[used++]=hex[value>>4];ssid[used++]=hex[value&15];
  }else ssid[used++]=(char)value;
 }
 written=snprintf(buffer,sizeof(buffer),"{\"revision\":\"%s\",\"configured\":%s,\"enabled\":%s,\"key_present\":%s,\"ssid\":\"%s\",\"gateway\":\"%s\",\"mask\":\"%s\",\"first\":\"%s\",\"last\":\"%s\"}",
  revision,view->key_present?"true":"false",view->enabled?"true":"false",view->key_present?"true":"false",
  ssid,view->gateway,view->mask,view->first,view->last);
 if(written<=0||(size_t)written>=sizeof(buffer)||(size_t)written+1>capacity)goto done;
 memcpy(out,buffer,(size_t)written+1);length=written;
 done:wr_iot_saved_wipe(buffer,sizeof(buffer));wr_iot_saved_wipe(ssid,sizeof(ssid));return length;
}
#endif
