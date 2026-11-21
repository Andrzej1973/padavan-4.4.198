#include "child-family-close-snapshot.h"
#include <assert.h>
int main(void){
 struct wr_iot_interface_ref refs[3];unsigned int n=99;int dev[3];
 for(unsigned i=0;i<3;i++){wr_iot_ref_init(&refs[i],&dev[i],i+1);refs[i].family=WR_REF_FAMILY_MBSS;refs[i].published=1;refs[i].last_token=1;refs[i].close_stage=4;}
 assert(wr_iot_child_family_close_snapshot(refs,3,WR_REF_FAMILY_MBSS,0,0,1,&n)&&n==3);
 refs[2].close_stage=3;n=99;assert(!wr_iot_child_family_close_snapshot(refs,3,WR_REF_FAMILY_MBSS,0,0,1,&n)&&n==99);
 refs[2].close_stage=4;assert(!wr_iot_child_family_close_snapshot(refs,3,WR_REF_FAMILY_MBSS,0,1,1,&n));
 assert(!wr_iot_child_family_close_snapshot(refs,3,WR_REF_FAMILY_MBSS,0,0,0,&n));
 refs[1].removing=1;assert(!wr_iot_child_family_close_snapshot(refs,3,WR_REF_FAMILY_MBSS,0,0,1,&n));
 refs[1].removing=0;refs[0].family=WR_REF_FAMILY_APCLI;
 assert(!wr_iot_child_family_close_snapshot(refs,3,WR_REF_FAMILY_APCLI,0,0,1,&n));
 refs[0].open_unmutated=1;assert(wr_iot_child_family_close_snapshot(refs,3,WR_REF_FAMILY_APCLI,0,0,1,&n)&&n==1);
 struct wr_iot_family_close states[3]={{0}};
 refs[0].open_unmutated=0;refs[0].close_stage=2;refs[0].close_serial=7;refs[0].close_epoch=9;
 states[0]=(struct wr_iot_family_close){refs[0].device,refs[0].generation,7,9,refs[0].last_token,WR_REF_FAMILY_APCLI,WR_FAMILY_CLOSE_DONE};
 assert(wr_iot_child_family_close_snapshot(refs,3,WR_REF_FAMILY_APCLI,states,0,1,&n)&&n==1);
 states[0].epoch++;assert(!wr_iot_child_family_close_snapshot(refs,3,WR_REF_FAMILY_APCLI,states,0,1,&n));states[0].epoch--;
 states[0].generation++;assert(!wr_iot_child_family_close_snapshot(refs,3,WR_REF_FAMILY_APCLI,states,0,1,&n));states[0].generation--;
 states[0].token++;assert(!wr_iot_child_family_close_snapshot(refs,3,WR_REF_FAMILY_APCLI,states,0,1,&n));states[0].token--;
 states[0].phase=WR_FAMILY_CLOSE_UNCERTAIN;assert(!wr_iot_child_family_close_snapshot(refs,3,WR_REF_FAMILY_APCLI,states,0,1,&n));
 return 0;
}
