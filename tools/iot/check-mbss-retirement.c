#include "mbss-retirement.h"
#include <assert.h>
int main(void){
 struct wr_bss_retirement b[2];
 wr_bss_retirement_init(&b[0]);wr_bss_retirement_init(&b[1]);
 assert(wr_bss_retirement_family_done(b,2));
 assert(wr_bss_retirement_publish(&b[0],1));
 assert(wr_bss_retirement_publish(&b[1],2));
 assert(!wr_bss_retirement_family_done(b,2));
 assert(!wr_bss_retirement_begin(&b[0],1,0));
 assert(wr_bss_retirement_begin(&b[0],1,1));
 assert(wr_bss_retirement_beacon_done(&b[0],1));
 assert(!wr_bss_retirement_abort_unmutated(&b[0],1,1));
 assert(!wr_bss_retirement_needs_beacon(&b[0],1));
 assert(wr_bss_retirement_kernel_done(&b[0],1));
 assert(wr_bss_retirement_vendor_done(&b[0],1));
 assert(!wr_bss_retirement_family_done(b,2));
 assert(wr_bss_retirement_begin(&b[1],2,1));
 /* Second beacon refusal: first BSS cannot repeat deinit on retry. */
 assert(!wr_bss_retirement_needs_beacon(&b[0],1));
 assert(wr_bss_retirement_needs_beacon(&b[1],2));
 assert(!wr_bss_retirement_beacon_done(&b[1],1));
 assert(!wr_bss_retirement_release(&b[0],1,0));
 assert(wr_bss_retirement_beacon_done(&b[1],2));
 assert(wr_bss_retirement_kernel_done(&b[1],2));
 assert(wr_bss_retirement_vendor_done(&b[1],2));
 assert(wr_bss_retirement_family_done(b,2));
 assert(wr_bss_retirement_release(&b[0],1,1));
 assert(wr_bss_retirement_release(&b[1],2,1));
 assert(!wr_bss_retirement_begin(&b[0],1,1));
 assert(wr_bss_retirement_publish(&b[0],3));
 assert(wr_bss_retirement_begin(&b[0],3,1));
 assert(wr_bss_retirement_abort_unmutated(&b[0],3,1));
 assert(b[0].stage==WR_BSS_LIVE);
 return 0;
}
