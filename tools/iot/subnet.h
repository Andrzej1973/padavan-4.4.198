/* Caller supplies every active LAN/WAN/VPN subnet before enabling IoT. */
#ifndef WR_IOT_SUBNET_H
#define WR_IOT_SUBNET_H
#include <stdint.h>
#include <stddef.h>
#include <arpa/inet.h>
#include "types.h"
static int wr_iot_ipv4(const char *s,uint32_t *value) {
 struct in_addr a;
 if(!s||inet_pton(AF_INET,s,&a)!=1)return 0;
 *value=ntohl(a.s_addr);return 1;
}
static int wr_iot_subnet_plan(struct wr_iot_subnet *out,const char *gateway,const char *mask,
 const char *start,const char *end,const struct wr_iot_range *reserved,size_t count) {
 struct wr_iot_subnet p;uint32_t inverse;size_t i;
 if(!out||(count&&!reserved))return 0;
 if(!wr_iot_ipv4(gateway,&p.gateway)||!wr_iot_ipv4(mask,&p.mask)||
    !wr_iot_ipv4(start,&p.start)||!wr_iot_ipv4(end,&p.end))return 0;
 inverse=~p.mask;
 /* Contiguous /16 through /30 only, with real host and DHCP addresses. */
 if(inverse<3||inverse>65535||(inverse&(inverse+1)))return 0;
 p.network=p.gateway&p.mask;p.broadcast=p.network|inverse;
 if(p.gateway<=p.network||p.gateway>=p.broadcast)return 0;
 if(!((p.network>>24)==10||(p.network>>20)==0xac1||(p.network>>16)==0xc0a8))return 0;
 if(p.start<=p.network||p.end>=p.broadcast||p.start>p.end)return 0;
 if(p.gateway>=p.start&&p.gateway<=p.end)return 0;
 for(i=0;i<count;i++) {
  if(reserved[i].first>reserved[i].last)return 0;
  if(p.network<=reserved[i].last&&reserved[i].first<=p.broadcast)return 0;
 }
 *out=p;return 1;
}
#endif
