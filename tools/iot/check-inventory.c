#include "inventory.h"
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
 puts("PASS bounded interface inventory, deduplication, subnet conflict, overflow preservation and read-only kernel snapshot; routed VPN prefix collection pending");return 0;
}
