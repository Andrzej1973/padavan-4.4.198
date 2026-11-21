/* Private RC conversion only: toggle captured settings, never edit or save. */
#ifndef WR_IOT_CONFIG_RUNTIME_REQUEST_H
#define WR_IOT_CONFIG_RUNTIME_REQUEST_H
#include "saved-config.h"
static inline int wr_iot_config_runtime_request(struct wr_iot_request *out,
 const struct wr_iot_saved_config *resolved,const char *captured_record)
{
 struct wr_iot_saved_config captured={0},normalized={0};
 struct wr_iot_request request={0};char record[WR_IOT_SAVED_CONFIG_MAX]={0};int ok=0;
 if(!out||!resolved||!captured_record||
    !memchr(captured_record,0,WR_IOT_SAVED_CONFIG_MAX)||
    !wr_iot_saved_config_decode(&captured,captured_record,strlen(captured_record)))goto done;
 normalized=*resolved;normalized.profile.enabled=captured.profile.enabled;
 if(!wr_iot_saved_config_encode(record,sizeof(record),&normalized)||strcmp(record,captured_record))goto done;
 if(resolved->profile.enabled==1)request=resolved->profile;
 else if(resolved->profile.enabled!=0)goto done;
 /* Runtime OFF is the existing empty envelope; retained active ownership,
  * not new desired credentials, supplies the backend's close identity. */
 *out=request;ok=1;
 done:wr_iot_saved_wipe(&captured,sizeof(captured));wr_iot_saved_wipe(&normalized,sizeof(normalized));
 wr_iot_saved_wipe(&request,sizeof(request));wr_iot_saved_wipe(record,sizeof(record));return ok;
}
#endif
