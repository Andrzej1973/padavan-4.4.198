/* Candidate request planner only. No ioctl, flash, service or production hook. */
#ifndef WR_MODERN_GUEST_BATCH_H
#define WR_MODERN_GUEST_BATCH_H
#include "guest-adapter.h"
#include "nvram-batch-wire.h"
static void wr_modern_guest_batch_wipe(void *memory,size_t size)
{volatile unsigned char *p=memory;while(size--)*p++=0;}
static int wr_modern_guest_batch_string(char *out,size_t size,const char *value)
{
 size_t length;if(!value)return 0;
 for(length=0;length<size&&value[length];length++){}
 if(length>=size)return 0;
 memcpy(out,value,length+1);return 1;
}
static enum wr_shared_wifi_result wr_modern_guest_build_batch(
 struct wr_nvram_wire_request *out,wr_modern_guest_read cgi,
 wr_modern_guest_read nv,void *context,enum wr_modern_guest_error *reason)
{
 struct wr_modern_guest_plan plan={0};struct wr_nvram_wire_request packet={0};
 struct wr_nvram_wire_item *item;char expected_key[64];const char *value;
 unsigned int i;enum wr_shared_wifi_result result;
 if(!out){if(reason)*reason=WR_GUEST_ERROR_INVALID;return WR_SHARED_WIFI_MISSING;}
 result=wr_modern_guest_admit_reason(&plan,cgi,nv,context,reason);
 if(result!=WR_SHARED_WIFI_OK)goto done;
 packet.version=WR_NVRAM_WIRE_VERSION;packet.count=13;
 for(i=0;i<13;i++){
  item=&packet.items[i];item->flags=1U; /* Compare every public snapshot key. */
  snprintf(item->name,sizeof(item->name),"%s_guest_%s",plan.band,wr_modern_guest_fields[i]);
  snprintf(expected_key,sizeof(expected_key),"wr_modern_guest_expected_%s",wr_modern_guest_fields[i]);
  if(!wr_modern_guest_batch_string(item->expected,sizeof(item->expected),cgi(context,expected_key)))goto invalid;
  value=cgi(context,item->name);
  if(value){
   item->flags|=2U;
   if(!wr_modern_guest_batch_string(item->value,sizeof(item->value),value))goto invalid;
  }
 }
 if(plan.has_key){
  item=&packet.items[packet.count++];
  snprintf(item->name,sizeof(item->name),"%s_guest_wpa_psk",plan.band);
  /* Keep checks the owned admitted key, never rewrites it. A concurrent key
   * change rejects the whole batch. Explicit change intentionally replaces it. */
  item->flags=plan.keep?1U:2U;
  if(!wr_modern_guest_batch_string(plan.keep?item->expected:item->value,
                                 sizeof(item->value),plan.key))goto invalid;
 }
 *out=packet;result=WR_SHARED_WIFI_OK;goto done;
invalid:
 if(reason)*reason=WR_GUEST_ERROR_INVALID;
 result=WR_SHARED_WIFI_SECURITY;
done:
 wr_modern_guest_clear(&plan);wr_modern_guest_batch_wipe(&packet,sizeof(packet));
 return result;
}
#endif
