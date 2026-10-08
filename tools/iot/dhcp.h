/* Candidate fragment for the existing dnsmasq; activation requires bridge/firewall readiness. */
#ifndef WR_IOT_DHCP_H
#define WR_IOT_DHCP_H
#include "subnet.h"
#include <stdio.h>
#include <string.h>
static void wr_iot_address(char out[16],uint32_t value) {
 snprintf(out,16,"%u.%u.%u.%u",(unsigned)(value>>24),(unsigned)((value>>16)&255),
          (unsigned)((value>>8)&255),(unsigned)(value&255));
}
static int wr_iot_dhcp_fragment(char *out,size_t capacity,int enabled,int router_mode,
 const char *gateway,const char *mask,const char *start,const char *end,
 const struct wr_iot_range *reserved,size_t count) {
 struct wr_iot_subnet p;char g[16],m[16],s[16],e[16],text[512];int n;
 if(!out||!capacity)return 0;
 if(!enabled){out[0]=0;return 1;}
 if(!router_mode||!wr_iot_subnet_plan(&p,gateway,mask,start,end,reserved,count))return 0;
 wr_iot_address(g,p.gateway);wr_iot_address(m,p.mask);wr_iot_address(s,p.start);wr_iot_address(e,p.end);
 n=snprintf(text,sizeof(text),"interface=br-iot\ndhcp-range=set:wr-iot,%s,%s,%s,3600\n"
   "dhcp-option=tag:wr-iot,3,%s\ndhcp-option=tag:wr-iot,6,%s\n",s,e,m,g,g);
 if(n<0||(size_t)n>=sizeof(text)||(size_t)n>=capacity)return 0;
 memcpy(out,text,(size_t)n+1);return 1;
}
#endif
