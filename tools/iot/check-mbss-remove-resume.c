#include "mbss-remove-resume.h"
#include <assert.h>
int main(void){
 struct wr_iot_interface_ref r={0};
 struct wr_bss_retirement b={0};
 int dev=0;
#define next(g,c) wr_iot_mbss_remove_next(&r,&b,&dev,g,c,1)
 /* The helper supplies a hypothetical proved report drain only to exercise
  * later stages. Current v25b has no such proof and cannot call them. */
 wr_iot_ref_init(&r,&dev,7);r.family=WR_REF_FAMILY_MBSS;r.published=1;
 wr_bss_retirement_init(&b);
 assert(wr_bss_retirement_publish(&b,7));
 assert(wr_iot_registry_begin_remove(&r,&dev,7));
 assert(wr_bss_retirement_begin(&b,7,1));
 assert(next(8,1)==WR_MBSS_REMOVE_WAIT);
 r.family=WR_REF_FAMILY_WDS;
 assert(next(7,1)==WR_MBSS_REMOVE_WAIT);
 r.family=WR_REF_FAMILY_MBSS;
 r.phase=WR_REF_CLOSING;r.last_token=1;
 assert(next(7,1)==WR_MBSS_REMOVE_WAIT);
 r.phase=WR_REF_IDLE;r.close_stage=4;
 assert(next(7,1)==WR_MBSS_REMOVE_BEACON);
 assert(wr_bss_retirement_beacon_done(&b,7));
 r.phase=WR_REF_RESERVED;
 assert(next(7,1)==WR_MBSS_REMOVE_WAIT);
 r.phase=WR_REF_IDLE;
 assert(next(7,1)==WR_MBSS_REMOVE_UNREGISTER);
 assert(!wr_iot_registry_after_unregister(&r,&dev,7,0));
 assert(next(7,1)==WR_MBSS_REMOVE_UNREGISTER);
 assert(wr_iot_registry_after_unregister(&r,&dev,7,1));
 assert(next(7,1)==WR_MBSS_REMOVE_RECORD_KERNEL);
 assert(wr_bss_retirement_kernel_done(&b,7));
 r.phase=WR_REF_CLOSING;r.last_token=1;
 assert(next(7,1)==WR_MBSS_REMOVE_WAIT);
 r.phase=WR_REF_IDLE;r.close_stage=4;
 assert(next(7,0)==WR_MBSS_REMOVE_WAIT);
 assert(wr_iot_mbss_remove_next(&r,&b,&dev,7,1,0)==WR_MBSS_REMOVE_WAIT);
 assert(next(7,1)==WR_MBSS_REMOVE_VENDOR);
 assert(wr_bss_retirement_vendor_done(&b,7));
 assert(next(7,0)==WR_MBSS_REMOVE_WAIT);
 assert(wr_iot_mbss_remove_next(&r,&b,&dev,7,1,0)==WR_MBSS_REMOVE_WAIT);
 assert(next(7,1)==WR_MBSS_REMOVE_RELEASE);
 assert(next(8,1)==WR_MBSS_REMOVE_WAIT);
 r.phase=WR_REF_CLOSING;
 assert(!wr_iot_registry_finish_after_unregister(&r,&dev,7,1,1,1));
 r.phase=WR_REF_IDLE;r.close_stage=4;
 assert(!wr_iot_registry_finish_after_unregister(&r,&dev,7,1,1,0));
 assert(wr_iot_registry_finish_after_unregister(&r,&dev,7,1,1,1));
 assert(wr_bss_retirement_release(&b,7,1));
 assert(next(7,1)==WR_MBSS_REMOVE_WAIT);
 return 0;
}
