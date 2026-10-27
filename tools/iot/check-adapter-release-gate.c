#include "adapter-release-gate.h"
#include <assert.h>
#include <stdio.h>

int main(void){
 struct wr_child_teardown children;
 struct wr_iot_radio_transition radio;
 struct wr_iot_interface_ref refs[2];
 int dev=0;
 wr_child_teardown_init(&children);
 wr_iot_radio_transition_init(&radio);
 wr_iot_ref_init(&refs[0],0,0);
 wr_iot_ref_init(&refs[1],0,0);
 assert(wr_child_teardown_begin(&children,0,1));
 radio.retiring=1;radio.phase=WR_RADIO_DOWN;
 assert(wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1));
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,1,1,1));
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,1,0,1,1));
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,0,1));
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,0));
 wr_iot_ref_init(&refs[0],&dev,1);refs[0].published=1;
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1));
 assert(wr_iot_registry_begin_remove(&refs[0],&dev,1));
 assert(wr_iot_registry_kernel_done(&refs[0],&dev,1));
 assert(wr_iot_registry_vendor_done(&refs[0],&dev,1));
 assert(wr_iot_registry_release(&refs[0],&dev,1));
 radio.reset_pending=WR_RADIO_RESET_PDMA;
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1));
 radio.reset_pending=0;radio.busy=WR_RADIO_CLOSE;
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1));
 radio.busy=0;radio.phase=WR_RADIO_CLOSING;
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1));
 radio.phase=WR_RADIO_DOWN;
 assert(wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1));
 wr_child_teardown_init(&children);
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1));
 puts("PASS adapter release gate: no deferred owner or live radio/reference");
 return 0;
}
