#ifndef WR_IOT_CONFIG_EDIT_PIN_H
#define WR_IOT_CONFIG_EDIT_PIN_H
#include "saved-config-store.h"
#include "config-edit.h"
#include "config-view.h"
static inline int wr_iot_config_edit_capture_view(struct wr_iot_generation_config *pin,
 const char *id,unsigned long long created,struct wr_iot_config_view *out)
{
 struct wr_iot_saved_config config={0};struct wr_iot_config_view view={0};int ok=0;
 if(!out||!wr_iot_generation_config_capture(pin,id,created,&config))goto done;
 if((pin->present&&!wr_iot_config_view_read(&view,pin->record,strlen(pin->record)))||
    !wr_iot_generation_config_current(pin,id,created)){
  (void)wr_iot_generation_config_release(pin);goto done;
 }
 *out=view;ok=1;
 done:wr_iot_saved_wipe(&config,sizeof(config));
 wr_iot_saved_wipe(&view,sizeof(view));return ok;
}
static inline int wr_iot_config_edit_resolve_pin(const struct wr_iot_generation_config *pin,
 const char *id,unsigned long long created,const struct wr_iot_saved_config *fields,
 enum wr_iot_config_key_action action,struct wr_iot_saved_config *out)
{
 struct wr_iot_saved_config verified={0};char record[WR_IOT_SAVED_CONFIG_MAX]={0};int ok=0;
 if(!out||!fields||!wr_iot_generation_config_current(pin,id,created))goto done;
 if(pin->present){
  ok=wr_iot_config_edit_resolve(&verified,fields,action,pin->record,strlen(pin->record),
                               pin->record,strlen(pin->record));
 }else if(action==WR_IOT_CONFIG_KEY_REPLACE){
  ok=wr_iot_saved_config_encode(record,sizeof(record),fields)&&
     wr_iot_saved_config_decode(&verified,record,strlen(record));
 }
 if(ok)*out=verified;
 done:wr_iot_saved_wipe(&verified,sizeof(verified));
 wr_iot_saved_wipe(record,sizeof(record));return ok;
}
#endif
