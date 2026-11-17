#ifndef WR_IOT_CONFIG_VIEW_H
#define WR_IOT_CONFIG_VIEW_H
#include "saved-config.h"
struct wr_iot_config_view {
 int enabled,key_present;
 char ssid[33],gateway[16],mask[16],first[16],last[16];
};
static inline int wr_iot_config_view_padded(const char *field,size_t capacity)
{
 const char *end=memchr(field,0,capacity);size_t index;
 if(!end)return 0;
 for(index=(size_t)(end-field)+1;index<capacity;index++)if(field[index])return 0;
 return 1;
}
static inline int wr_iot_config_view_valid(const struct wr_iot_config_view *view)
{
 struct wr_iot_subnet subnet;
 if(!view||(view->enabled!=0&&view->enabled!=1)||(view->key_present!=0&&view->key_present!=1)||
    !wr_iot_config_view_padded(view->ssid,sizeof(view->ssid))||
    !wr_iot_config_view_padded(view->gateway,sizeof(view->gateway))||
    !wr_iot_config_view_padded(view->mask,sizeof(view->mask))||
    !wr_iot_config_view_padded(view->first,sizeof(view->first))||
    !wr_iot_config_view_padded(view->last,sizeof(view->last)))return 0;
 if(!view->key_present)return !view->enabled&&!view->ssid[0]&&!view->gateway[0]&&
  !view->mask[0]&&!view->first[0]&&!view->last[0];
 return wr_shared_wifi_text(view->ssid,1,32)&&
  wr_iot_subnet_plan(&subnet,view->gateway,view->mask,view->first,view->last,NULL,0);
}
static inline int wr_iot_config_view_read(struct wr_iot_config_view *out,
 const char *record,size_t length)
{
 struct wr_iot_saved_config decoded={0};struct wr_iot_config_view view={0};
 char canonical[WR_IOT_SAVED_CONFIG_MAX]={0};int ok=0;
 if(!out||!record||!length||length>=sizeof(canonical)||
    !wr_iot_saved_config_decode(&decoded,record,length)||
    !wr_iot_saved_config_encode(canonical,sizeof(canonical),&decoded)||
    strlen(canonical)!=length||memcmp(canonical,record,length))goto done;
 view.enabled=decoded.profile.enabled;view.key_present=1;
 memcpy(view.ssid,decoded.profile.ssid,sizeof(view.ssid));
 memcpy(view.gateway,decoded.profile.gateway,sizeof(view.gateway));
 memcpy(view.mask,decoded.profile.mask,sizeof(view.mask));
 memcpy(view.first,decoded.profile.first,sizeof(view.first));
 memcpy(view.last,decoded.profile.last,sizeof(view.last));
 *out=view;ok=1;
 done:
 wr_iot_saved_wipe(&decoded,sizeof(decoded));
 wr_iot_saved_wipe(canonical,sizeof(canonical));
 wr_iot_saved_wipe(&view,sizeof(view));return ok;
}
#endif
