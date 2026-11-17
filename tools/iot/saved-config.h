/* Complete provisioning data, including when requested runtime state is OFF.
 * One bounded record is suitable for a single native NVRAM SET. This codec
 * performs no writes, flash commits, radio actions or runtime admission.
 * Callers must serialize borrowed reads and provide live overlap ranges again
 * at activation. A decoded record is never proof of loaded driver identity.
 */
#ifndef WR_IOT_SAVED_CONFIG_H
#define WR_IOT_SAVED_CONFIG_H
#include "request.h"
#define WR_IOT_SAVED_CONFIG_MAX 384
#define WR_IOT_SAVED_CONFIG_VERSION "WR-IOT-CONFIG-1:"
struct wr_iot_saved_config { struct wr_iot_request profile; };
struct wr_iot_saved_fields { char values[7][65]; };

static inline const char *wr_iot_saved_field_read(void *context,const char *key)
{
 static const char *keys[]={"wr_iot_enable","wr_iot_ssid","wr_iot_psk",
  "wr_iot_gateway","wr_iot_mask","wr_iot_start","wr_iot_end"};
 struct wr_iot_saved_fields *fields=context;size_t i;
 if(!fields||!key)return NULL;
 for(i=0;i<7;i++)if(!strcmp(keys[i],key))return fields->values[i];
 return NULL;
}
static inline void wr_iot_saved_wipe(void *data,size_t length)
{volatile unsigned char *p=data;while(length--)*p++=0;}

/* Unlike runtime OFF, disabled provisioning still requires credentials and a
 * valid subnet. Never pass a zeroed runtime OFF request as saved configuration.
 * Failure leaves the caller's destination unchanged. */
static inline int wr_iot_saved_config_read(struct wr_iot_saved_config *out,
 const char *(*read)(void *,const char *),void *context,
 const struct wr_iot_range *reserved,size_t count)
{
 static const char *keys[]={"wr_iot_enable","wr_iot_ssid","wr_iot_psk",
  "wr_iot_gateway","wr_iot_mask","wr_iot_start","wr_iot_end"};
 static const size_t capacities[]={2,33,65,16,16,16,16};
 struct wr_iot_saved_fields fields={0};struct wr_iot_saved_config candidate={0};
 size_t i;int enabled=0,ok=0;
 if(!out||!read)return 0;
 for(i=0;i<7;i++)
  if(!wr_iot_request_copy(fields.values[i],capacities[i],read(context,keys[i])))goto done;
 if(strcmp(fields.values[0],"0")&&strcmp(fields.values[0],"1"))goto done;
 enabled=fields.values[0][0]=='1';fields.values[0][0]='1';
 /* This selects structural validation only, not permission to enable a BSS. */
 if(!wr_iot_request_read(&candidate.profile,wr_iot_saved_field_read,&fields,
                         1,1,0,reserved,count))goto done;
 candidate.profile.enabled=enabled;*out=candidate;ok=1;
 done:wr_iot_saved_wipe(&fields,sizeof(fields));
 wr_iot_saved_wipe(&candidate,sizeof(candidate));return ok;
}
static inline int wr_iot_saved_hex(unsigned char c)
{
 if(c>='0'&&c<='9')return c-'0';
 if(c>='a'&&c<='f')return c-'a'+10;
 return -1;
}
/* Canonical lowercase hex protects UTF-8, delimiters and shell metacharacters
 * in credentials from becoming syntax in exports. No shell parser is used. */
static inline int wr_iot_saved_config_decode(struct wr_iot_saved_config *out,
 const char *record,size_t length)
{
 struct wr_iot_saved_fields fields={0};size_t at,field=0,n=0;
 int high,low,ok=0;const size_t prefix=sizeof(WR_IOT_SAVED_CONFIG_VERSION)-1;
 if(!out||!record||length<=prefix||length>=WR_IOT_SAVED_CONFIG_MAX||
    memcmp(record,WR_IOT_SAVED_CONFIG_VERSION,prefix))return 0;
 for(at=prefix;at<length;){
  if(record[at]==':'){
   if(!n||field==6)goto done;
   field++;n=0;at++;continue;
  }
  if(at+1>=length||n+1>=sizeof(fields.values[0]))goto done;
  high=wr_iot_saved_hex((unsigned char)record[at]);
  low=wr_iot_saved_hex((unsigned char)record[at+1]);
  if(high<0||low<0||!(high||low))goto done;
  fields.values[field][n++]=(char)((high<<4)|low);at+=2;
 }
 if(field!=6||!n)goto done;
 ok=wr_iot_saved_config_read(out,wr_iot_saved_field_read,&fields,NULL,0);
 done:wr_iot_saved_wipe(&fields,sizeof(fields));return ok;
}
static inline int wr_iot_saved_config_encode(char *out,size_t capacity,
 const struct wr_iot_saved_config *config)
{
 static const char hex[]="0123456789abcdef";
 const struct wr_iot_request *r;const char *values[7];
 const size_t sizes[]={2,33,65,16,16,16,16};char enable[2]={0};
 char record[WR_IOT_SAVED_CONFIG_MAX]={0};struct wr_iot_saved_config checked={0};
 size_t at=sizeof(WR_IOT_SAVED_CONFIG_VERSION)-1,i,j;int ok=0;
 if(!out||!config)return 0;
 r=&config->profile;if(r->enabled!=0&&r->enabled!=1)return 0;
 enable[0]=r->enabled?'1':'0';values[0]=enable;values[1]=r->ssid;
 values[2]=r->password;values[3]=r->gateway;values[4]=r->mask;
 values[5]=r->first;values[6]=r->last;
 memcpy(record,WR_IOT_SAVED_CONFIG_VERSION,at);
 for(i=0;i<7;i++){
  if(!memchr(values[i],0,sizes[i]))goto done;
  if(i)record[at++]=':';
  for(j=0;values[i][j];j++){
   if(at+2>=sizeof(record))goto done;
   record[at++]=hex[(unsigned char)values[i][j]>>4];
   record[at++]=hex[(unsigned char)values[i][j]&15];
  }
 }
 if(at+1>capacity||!wr_iot_saved_config_decode(&checked,record,at))goto done;
 memcpy(out,record,at+1);ok=1;
 done:wr_iot_saved_wipe(record,sizeof(record));
 wr_iot_saved_wipe(&checked,sizeof(checked));return ok;
}
#endif
