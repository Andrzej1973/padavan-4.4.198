#include "route-prefix.h"
#include "subnet.h"
#include <assert.h>
#include <stdio.h>
int main(void) {
 struct wr_iot_inventory inventory,before;struct wr_iot_subnet subnet;size_t i;
 memset(&inventory,0,sizeof(inventory));
 assert(wr_iot_inventory_add(&inventory,0xc0a80101U,0xffffff00U));
 assert(wr_iot_inventory_add(&inventory,0xc0a801c8U,0xffffff00U)&&inventory.count==1);
 assert(wr_iot_inventory_add(&inventory,0x0a320001U,0xffffff00U));
 assert(wr_iot_inventory_add(&inventory,0xc0a83280U,0xffffffffU));
 assert(!wr_iot_subnet_plan(&subnet,"192.168.50.1","255.255.255.0","192.168.50.20","192.168.50.200",inventory.ranges,inventory.count));
 before=inventory;assert(!wr_iot_inventory_add(&inventory,1,0xff00ff00U));assert(!memcmp(&before,&inventory,sizeof(before)));
 assert(!wr_iot_inventory_add(&inventory,1,0));assert(!memcmp(&before,&inventory,sizeof(before)));
 memset(&inventory,0,sizeof(inventory));
 for(i=0;i<WR_IOT_INVENTORY_MAX;i++)assert(wr_iot_inventory_add(&inventory,0x0a000001U+(uint32_t)(i<<8),0xffffff00U));
 before=inventory;assert(!wr_iot_inventory_add(&inventory,0xac100001U,0xffffff00U));assert(!memcmp(&before,&inventory,sizeof(before)));
 assert(wr_iot_inventory_interfaces(&inventory,0));
 assert(inventory.count>0&&inventory.count<=WR_IOT_INVENTORY_MAX);
 {
  struct {struct nlmsghdr h;struct rtmsg route;struct rtattr dst;uint32_t address;} packet;
  memset(&packet,0,sizeof(packet));memset(&inventory,0,sizeof(inventory));
  packet.h.nlmsg_type=RTM_NEWROUTE;packet.h.nlmsg_len=sizeof(packet);
  packet.route.rtm_family=AF_INET;packet.route.rtm_type=RTN_UNICAST;packet.route.rtm_dst_len=24;
  packet.dst.rta_type=RTA_DST;packet.dst.rta_len=RTA_LENGTH(4);packet.address=htonl(0x0a320000U);
  assert(wr_iot_route_prefix(&inventory,&packet.h,sizeof(packet))&&inventory.count==1);
  assert(inventory.ranges[0].first==0x0a320000U&&inventory.ranges[0].last==0x0a3200ffU);
  before=inventory;packet.route.rtm_dst_len=33;
  assert(!wr_iot_route_prefix(&inventory,&packet.h,sizeof(packet)));assert(!memcmp(&inventory,&before,sizeof(before)));
  packet.route.rtm_dst_len=24;packet.h.nlmsg_flags=NLM_F_DUMP_INTR;
  assert(!wr_iot_route_prefix(&inventory,&packet.h,sizeof(packet)));
  packet.h.nlmsg_flags=0;packet.address=htonl(0x0a320001U);
  assert(!wr_iot_route_prefix(&inventory,&packet.h,sizeof(packet)));
  packet.address=htonl(0x0a320000U);packet.dst.rta_len=RTA_LENGTH(3);
  assert(!wr_iot_route_prefix(&inventory,&packet.h,sizeof(packet)));
 }
 puts("PASS bounded interface inventory, deduplication, subnet conflict, overflow preservation and read-only kernel snapshot; routed VPN prefix collection pending");return 0;
}
