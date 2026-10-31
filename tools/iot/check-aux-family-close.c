#include "aux-family-close.h"
#include <assert.h>
#include <stdio.h>

static void check_family(enum wr_iot_ref_family family){
 struct wr_iot_family_close state;
 struct wr_iot_interface_ref record;
 int device=0;
 wr_iot_ref_init(&record,&device,3);
 record.family=family;record.phase=WR_REF_CLOSING;record.close_serial=7;
 record.close_epoch=2;record.last_token=4;record.published=1;
 wr_iot_family_close_init(&state);
 assert(!wr_iot_family_down_begin(&state,&record));
 assert(wr_iot_family_close_begin(&state,&record));
 record.close_epoch++;
 assert(!wr_iot_family_close_result(&state,&record,1));record.close_epoch--;
 record.last_token++;
 assert(!wr_iot_family_close_result(&state,&record,1));record.last_token--;
 assert(!wr_iot_family_close_begin(&state,&record));
 assert(wr_iot_family_close_result(&state,&record,0));
 assert(state.phase==WR_FAMILY_CLOSE_UNCERTAIN);
 assert(!wr_iot_family_close_result(&state,&record,1));
 assert(!wr_iot_family_down_begin(&state,&record));
 assert(!wr_iot_family_close_finish(&state,&record));

 wr_iot_family_close_init(&state);
 assert(wr_iot_family_close_begin(&state,&record));
 assert(wr_iot_family_close_result(&state,&record,1));
 assert(wr_iot_family_down_begin(&state,&record));
 assert(wr_iot_family_down_result(&state,&record,0,1));
 assert(wr_iot_family_down_begin(&state,&record));
 record.close_serial=8;
 assert(!wr_iot_family_down_result(&state,&record,1,0));
 record.close_serial=7;
 assert(wr_iot_family_down_result(&state,&record,1,0));
 assert(wr_iot_family_close_finish(&state,&record));
 assert(!wr_iot_family_down_begin(&state,&record));
}
int main(void){
 struct wr_iot_family_close state;
 struct wr_iot_interface_ref record;
 int device=0;
 check_family(WR_REF_FAMILY_APCLI);
 check_family(WR_REF_FAMILY_MONITOR);
 wr_iot_ref_init(&record,&device,2);
 record.family=WR_REF_FAMILY_WDS;record.phase=WR_REF_CLOSING;
 record.close_serial=4;wr_iot_family_close_init(&state);
 assert(!wr_iot_family_close_begin(&state,&record));
 puts("PASS AP-client/monitor family close stages");
 return 0;
}
