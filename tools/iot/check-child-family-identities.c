#include "child-family-identities.h"
#include <assert.h>
int main(void){struct wr_iot_interface_ref refs[2];struct wr_iot_child_identity ids[2];unsigned int used=99;int dev[2];
for(unsigned i=0;i<2;i++){wr_iot_ref_init(&refs[i],&dev[i],i+1);refs[i].family=WR_REF_FAMILY_MBSS;refs[i].published=1;refs[i].last_token=1;refs[i].close_stage=4;}
assert(!wr_iot_child_family_capture(refs,2,WR_REF_FAMILY_MBSS,0,0,1,ids,1,&used)&&used==99);
assert(wr_iot_child_family_capture(refs,2,WR_REF_FAMILY_MBSS,0,0,1,ids,2,&used)&&used==2);
assert(!wr_iot_child_family_registry_empty(refs,2,WR_REF_FAMILY_MBSS,ids,used));
wr_iot_ref_init(&refs[0],0,0);assert(!wr_iot_child_family_registry_empty(refs,2,WR_REF_FAMILY_MBSS,ids,used));
wr_iot_ref_init(&refs[1],0,0);assert(wr_iot_child_family_registry_empty(refs,2,WR_REF_FAMILY_MBSS,ids,used));
wr_iot_ref_init(&refs[0],&dev[0],99);refs[0].family=WR_REF_FAMILY_WDS;assert(!wr_iot_child_family_registry_empty(refs,2,WR_REF_FAMILY_MBSS,ids,used));
return 0;}
