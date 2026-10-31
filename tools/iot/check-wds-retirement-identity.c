#include "wds-peer-operation.h"
#include <stdio.h>
#include <stdlib.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"failed %d: %s\n",__LINE__,#x);exit(42);}}while(0)
int main(void)
{
 struct wr_iot_wds_peer_operation s;
 int device=0,other=0;
 unsigned char addr[6]={1,2,3,4,5,6},wrong[6]={6,5,4,3,2,1};
 unsigned long first,second;
 wr_iot_wds_peer_operation_init(&s,&device,7);
 CHECK(!wr_iot_wds_retirement_save(&s,&device,7,0,1,addr));
 CHECK(wr_iot_wds_peer_operation_begin_remove(&s,&device,7));
 first=wr_iot_wds_retirement_save(&s,&device,7,0,1,addr);CHECK(first==1);
 CHECK(!wr_iot_wds_retirement_save(&s,&device,7,0,1,addr));
 CHECK(!wr_iot_wds_retirement_matches(&s,&other,7,first,0,1,addr));
 CHECK(!wr_iot_wds_retirement_matches(&s,&device,8,first,0,1,addr));
 CHECK(!wr_iot_wds_retirement_matches(&s,&device,7,first,1,1,addr));
 CHECK(!wr_iot_wds_retirement_matches(&s,&device,7,first,0,2,addr));
 CHECK(!wr_iot_wds_retirement_matches(&s,&device,7,first,0,1,wrong));
 CHECK(wr_iot_wds_retirement_matches(&s,&device,7,first,0,1,addr));
 CHECK(wr_iot_wds_retirement_complete(&s,first));
 CHECK(!wr_iot_wds_retirement_complete(&s,first));
 CHECK(wr_iot_wds_peer_operation_begin_remove(&s,&device,7));
 second=wr_iot_wds_retirement_save(&s,&device,7,0,1,addr);CHECK(second==2);
 CHECK(!wr_iot_wds_retirement_complete(&s,first)&&s.retirement_stage==1);
 CHECK(wr_iot_wds_retirement_retain(&s,second));
 CHECK(!wr_iot_wds_retirement_retain(&s,second));
 CHECK(!wr_iot_wds_retirement_complete(&s,second)); /* no unchecked retained release */
 CHECK(s.removing&&s.retirement_stage==2&&s.retirement_serial==second);
 puts("PASS saved WDS retirement identity and stale serial refusal");return 0;
}
