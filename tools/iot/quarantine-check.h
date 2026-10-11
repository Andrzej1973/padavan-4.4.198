/* Validate a complete, bounded iptables-save/ip6tables-save snapshot without
 * counters. Caller must obtain it from the live kernel using a checked command.
 * This checks quarantine only, not the active DHCP/DNS/WAN allow policy. */
#ifndef WR_IOT_QUARANTINE_CHECK_H
#define WR_IOT_QUARANTINE_CHECK_H
#include <stddef.h>
#include <string.h>
static inline int wr_iot_quarantine_snapshot(const char *data,size_t size){
 static const char *const input[]={"-A INPUT -i br-iot -j DROP","-A INPUT -i ra2 -j DROP"};
 static const char *const forward[]={"-A FORWARD -i br-iot -j DROP","-A FORWARD -o br-iot -j DROP",
  "-A FORWARD -i ra2 -j DROP","-A FORWARD -o ra2 -j DROP"};
 size_t offset=0,used,in=0,fwd=0;int filter=0,seen=0,committed=0;
 char line[1024];
 if(!data||!size||size>256U*1024U||memchr(data,0,size))return 0;
 while(offset<size){
  const char *end=memchr(data+offset,'\n',size-offset);
  if(!end)return 0;
  used=(size_t)(end-data)-offset;
  if(used>=sizeof(line))return 0;
  memcpy(line,data+offset,used);line[used]=0;offset+=used+1;
  if(!used||line[0]=='#')continue;
  if(line[0]=='*'){
   if(filter)return 0;
   filter=!strcmp(line,"*filter");
   if(filter&&seen++)return 0;
   continue;
  }
  if(!strcmp(line,"COMMIT")){
   if(filter){if(in!=2||fwd!=4)return 0;committed=1;filter=0;}
   continue;
  }
  if(!filter)continue;
  if(line[0]==':')continue;
  if(strncmp(line,"-A ",3))return 0;
  if(!strncmp(line,"-A INPUT ",9)&&in<2){if(strcmp(line,input[in++]))return 0;}
  if(!strncmp(line,"-A FORWARD ",11)&&fwd<4){if(strcmp(line,forward[fwd++]))return 0;}
 }
 return seen==1&&committed&&!filter;
}
#endif
