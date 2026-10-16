#ifndef WR_USBIP_EXPORT_RULES_H
#define WR_USBIP_EXPORT_RULES_H
/* Validation only. Does not write settings, claim devices or schedule exports. */
#include <stddef.h>
#include <string.h>
#define WR_USBIP_EXPORT_RULES 16
struct wr_usbip_export_rule {
 unsigned enabled;
 char bus[32],vendor[5],product[5],serial_hex[513];
};
enum wr_usbip_export_error {
 WR_USBIP_EXPORT_OK=0,WR_USBIP_EXPORT_INVALID,WR_USBIP_EXPORT_DUPLICATE_PORT,
 WR_USBIP_EXPORT_DUPLICATE_IDENTITY
};
static inline int wr_usbip_export_hex(const char *text,size_t size,int serial)
{
 size_t n,i;
 if(!memchr(text,0,size))return 0;
 n=strlen(text);
 if(!n || (serial ? n%2 : n!=4))return 0;
 for(i=0;i<n;i++)if(!strchr("0123456789abcdef",text[i]))return 0;
 if(serial)for(i=0;i<n;i+=2)
  if(text[i]=='0'||text[i]=='1'||(text[i]=='7'&&text[i+1]=='f'))return 0;
 return 1;
}
static inline int wr_usbip_export_bus(const char text[32])
{
 const char *p=text;
 if(!memchr(text,0,32)||*p<'0'||*p>'9')return 0;
 while(*p>='0'&&*p<='9')p++;
 if(*p++!='-'||*p<'0'||*p>'9')return 0;
 for(;;){
  while(*p>='0'&&*p<='9')p++;
  if(!*p)return 1;
  if(*p++!='.'||*p<'0'||*p>'9')return 0;
 }
}
static inline enum wr_usbip_export_error wr_usbip_export_validate(
 const struct wr_usbip_export_rule *rules,size_t count,size_t *bad_slot)
{
 size_t i,j;
 if(bad_slot)*bad_slot=(size_t)-1;
 if(!rules||count>WR_USBIP_EXPORT_RULES)return WR_USBIP_EXPORT_INVALID;
 for(i=0;i<count;i++){
  const struct wr_usbip_export_rule *r=rules+i;
  if(bad_slot)*bad_slot=i;
  if(r->enabled>1)return WR_USBIP_EXPORT_INVALID;
  if(!r->enabled)continue;
  if(!wr_usbip_export_bus(r->bus)||!wr_usbip_export_hex(r->vendor,sizeof(r->vendor),0)||
     !wr_usbip_export_hex(r->product,sizeof(r->product),0)||
     !wr_usbip_export_hex(r->serial_hex,sizeof(r->serial_hex),1))return WR_USBIP_EXPORT_INVALID;
  for(j=0;j<i;j++)if(rules[j].enabled){
   if(!strcmp(rules[j].bus,r->bus))return WR_USBIP_EXPORT_DUPLICATE_PORT;
   if(!strcmp(rules[j].vendor,r->vendor)&&!strcmp(rules[j].product,r->product)&&
      !strcmp(rules[j].serial_hex,r->serial_hex))return WR_USBIP_EXPORT_DUPLICATE_IDENTITY;
  }
 }
 if(bad_slot)*bad_slot=(size_t)-1;
 return WR_USBIP_EXPORT_OK;
}
#endif
