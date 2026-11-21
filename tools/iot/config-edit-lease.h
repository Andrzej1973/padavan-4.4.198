#ifndef WR_IOT_CONFIG_EDIT_LEASE_H
#define WR_IOT_CONFIG_EDIT_LEASE_H
#include "config-edit-pin.h"
#include "control-record-common.h"
enum wr_iot_edit_lease_phase {WR_IOT_EDIT_LEASE_LIVE=1,WR_IOT_EDIT_LEASE_CLAIMED,WR_IOT_EDIT_LEASE_INVALID};
struct wr_iot_config_edit_lease {
 struct wr_iot_generation_config pin;
 unsigned long long deadline,last_clock;
 enum wr_iot_edit_lease_phase phase;
};
static inline int wr_iot_config_edit_lease_open(struct wr_iot_config_edit_lease *lease,
 unsigned long long now,unsigned int lifetime,
 int (*entropy)(void *,unsigned char *,unsigned int),void *context,
 struct wr_iot_config_view *out,char revision[33])
{
 static const char hex[]="0123456789abcdef";
 unsigned char bytes[32]={0},nonzero=0;char id[33]={0};
 struct wr_iot_config_view view={0};size_t index;int ok=0;
 if(!lease||!out||!revision||!entropy||!now||!lifetime||lifetime>300||
    now>~0ULL-lifetime||lease->phase||lease->deadline||lease->last_clock||
    lease->pin.owner||entropy(context,bytes,sizeof(bytes))!=sizeof(bytes))goto done;
 for(index=0;index<16;index++){
  nonzero|=bytes[index];id[index*2]=hex[bytes[index]>>4];id[index*2+1]=hex[bytes[index]&15];
 }
 if(!nonzero||!wr_iot_config_edit_capture_view(&lease->pin,id,now,&view))goto done;
 lease->deadline=now+lifetime;lease->last_clock=now;lease->phase=WR_IOT_EDIT_LEASE_LIVE;
 *out=view;memcpy(revision,id,sizeof(id));ok=1;
 done:wr_iot_saved_wipe(bytes,sizeof(bytes));wr_iot_saved_wipe(id,sizeof(id));
 wr_iot_saved_wipe(&view,sizeof(view));return ok;
}
static inline int wr_iot_config_edit_lease_claim(struct wr_iot_config_edit_lease *lease,
 const char *revision,unsigned long long now,const struct wr_iot_saved_config *fields,
 enum wr_iot_config_key_action action,struct wr_iot_saved_config *out)
{
 struct wr_iot_saved_config config={0};int ok=0;
 if(!lease||!fields||!out||lease->phase!=WR_IOT_EDIT_LEASE_LIVE||
    !wr_iot_generation_config_owned(&lease->pin)||!wr_iot_control_id(revision)||
    strcmp(revision,lease->pin.id))goto done;
 if(now<lease->last_clock||now>=lease->deadline||
    !wr_iot_config_edit_resolve_pin(&lease->pin,revision,lease->pin.created,fields,action,&config)){
  lease->phase=WR_IOT_EDIT_LEASE_INVALID;goto done;
 }
 lease->phase=WR_IOT_EDIT_LEASE_CLAIMED;lease->last_clock=now;*out=config;ok=1;
 done:wr_iot_saved_wipe(&config,sizeof(config));return ok;
}
static inline int wr_iot_config_edit_lease_release(struct wr_iot_config_edit_lease *lease)
{
 if(!lease||lease->phase<WR_IOT_EDIT_LEASE_LIVE||lease->phase>WR_IOT_EDIT_LEASE_INVALID||
    !wr_iot_generation_config_release(&lease->pin))return 0;
 wr_iot_saved_wipe(lease,sizeof(*lease));return 1;
}
#endif
