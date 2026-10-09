#include "network-check.h"
#include "bridge.h"
#include "route-snapshot.h"
#include "subnet.h"
int wr_iot_network_check(const char *gateway,const char *mask,const char *start,const char *end) {
 struct wr_iot_inventory inventory;struct wr_iot_subnet plan;unsigned int owned_index=0;
 if(!wr_iot_subnet_plan(&plan,gateway,mask,start,end,NULL,0))return 0;
 if(wr_iot_bridge_is_owned()) {
  owned_index=if_nametoindex("br-iot");if(!owned_index)return 0;
 }
 if(!wr_iot_inventory_interfaces(&inventory,owned_index!=0)||
    !wr_iot_route_snapshot_owned(&inventory,owned_index,plan.network,plan.mask))return 0;
 return wr_iot_subnet_plan(&plan,gateway,mask,start,end,inventory.ranges,inventory.count);
}
