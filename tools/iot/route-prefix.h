/* Decode kernel route prefixes; acquisition/serialization belongs to the caller. */
#ifndef WR_IOT_ROUTE_PREFIX_H
#define WR_IOT_ROUTE_PREFIX_H
#include "inventory.h"
#include <linux/rtnetlink.h>
static int wr_iot_route_prefix(struct wr_iot_inventory *out,const struct nlmsghdr *message,size_t available) {
 const struct rtmsg *route;struct rtattr *attribute;struct wr_iot_inventory candidate;
 uint32_t address=0,mask;int length,seen=0;
 if(!out||!message||available<sizeof(*message)||message->nlmsg_len>available||
    message->nlmsg_len<NLMSG_LENGTH(sizeof(*route))||message->nlmsg_type!=RTM_NEWROUTE||
    (message->nlmsg_flags&NLM_F_DUMP_INTR))return 0;
 route=(const struct rtmsg *)NLMSG_DATA(message);
 if(route->rtm_family!=AF_INET)return 1;
 if(route->rtm_dst_len>32)return 0;
 length=RTM_PAYLOAD(message);
 for(attribute=RTM_RTA(route);RTA_OK(attribute,length);attribute=RTA_NEXT(attribute,length)) {
  if(attribute->rta_type==RTA_DST) {
   uint32_t wire;
   if(seen||RTA_PAYLOAD(attribute)!=sizeof(wire))return 0;
   memcpy(&wire,RTA_DATA(attribute),sizeof(wire));address=ntohl(wire);seen=1;
  }
 }
 if(length)return 0;
 /* Default routes express egress policy, not ownership of every IPv4 address. */
 if(!route->rtm_dst_len)return address==0;
 if(!seen)return 0;
 if(route->rtm_type!=RTN_UNICAST)return 1;
 mask=0xffffffffU<<(32-route->rtm_dst_len);
 if(address&~mask)return 0;
 candidate=*out;
 if(!wr_iot_inventory_add(&candidate,address,mask))return 0;
 *out=candidate;return 1;
}
#endif
