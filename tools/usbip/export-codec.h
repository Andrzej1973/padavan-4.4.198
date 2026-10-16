#ifndef WR_USBIP_EXPORT_CODEC_H
#define WR_USBIP_EXPORT_CODEC_H
/* Private settings format; no file I/O or device changes. */
#include <stdio.h>
#include "export-rules.h"
#define WR_USBIP_EXPORT_TEXT_MAX 9216
#define WR_USBIP_EXPORT_MAGIC "wr-usbip-exports-v1\n"
static inline int wr_usbip_export_encode(const struct wr_usbip_export_rule *rules,
 char *text,size_t capacity)
{
 size_t i,used;int n;
 if(!text||wr_usbip_export_validate(rules,16,NULL)!=WR_USBIP_EXPORT_OK)return 0;
 n=snprintf(text,capacity,"%s",WR_USBIP_EXPORT_MAGIC);
 if(n<0||(size_t)n>=capacity)return 0;
 used=(size_t)n;
 for(i=0;i<16;i++){
  const struct wr_usbip_export_rule *r=rules+i;
  n=r->enabled?snprintf(text+used,capacity-used,"1\t%s\t%s\t%s\t%s\n",
     r->bus,r->vendor,r->product,r->serial_hex):snprintf(text+used,capacity-used,"0\n");
  if(n<0||(size_t)n>=capacity-used)return 0;
  used+=(size_t)n;
 }
 return used<WR_USBIP_EXPORT_TEXT_MAX;
}
static inline int wr_usbip_export_decode(const char *text,size_t length,
 struct wr_usbip_export_rule *out)
{
 struct wr_usbip_export_rule candidate[16];size_t i,offset=sizeof(WR_USBIP_EXPORT_MAGIC)-1;
 if(!text||!out||length<offset||length>=WR_USBIP_EXPORT_TEXT_MAX||memchr(text,0,length)||
    memcmp(text,WR_USBIP_EXPORT_MAGIC,offset))return 0;
 memset(candidate,0,sizeof(candidate));
 for(i=0;i<16;i++){
  char line[560],*field[5],*p;size_t n,j;const char *end;
  if(offset>=length)return 0;
  end=memchr(text+offset,'\n',length-offset);if(!end)return 0;
  n=(size_t)(end-(text+offset));if(n>=sizeof(line))return 0;
  memcpy(line,text+offset,n);line[n]=0;offset+=n+1;
  if(!strcmp(line,"0"))continue;
  p=line;field[0]=p;
  for(j=1;j<5;j++){p=strchr(p,'\t');if(!p)return 0;*p++=0;field[j]=p;}
  if(strcmp(field[0],"1")||strchr(field[4],'\t'))return 0;
  if(strlen(field[1])>=sizeof(candidate[i].bus)||strlen(field[2])>=sizeof(candidate[i].vendor)||
     strlen(field[3])>=sizeof(candidate[i].product)||strlen(field[4])>=sizeof(candidate[i].serial_hex))return 0;
  candidate[i].enabled=1;strcpy(candidate[i].bus,field[1]);strcpy(candidate[i].vendor,field[2]);
  strcpy(candidate[i].product,field[3]);strcpy(candidate[i].serial_hex,field[4]);
 }
 if(offset!=length||wr_usbip_export_validate(candidate,16,NULL)!=WR_USBIP_EXPORT_OK)return 0;
 memcpy(out,candidate,sizeof(candidate));return 1;
}
#endif
