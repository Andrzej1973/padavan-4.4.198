#include "beacon-producer-gate.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
 struct wr_iot_beacon_producer_gate g;
 wr_iot_beacon_gate_init(&g);
 assert(!wr_iot_beacon_gate_begin(&g,1));
 assert(!wr_iot_beacon_gate_open(&g,0));
 assert(wr_iot_beacon_gate_open(&g,1));
 assert(wr_iot_beacon_gate_begin(&g,1)); /* pointer acquired */
 assert(wr_iot_beacon_gate_submit(&g,1));
 assert(wr_iot_beacon_gate_revoke(&g,1)); /* close races with preparation */
 assert(!wr_iot_beacon_gate_begin(&g,1));
 assert(!wr_iot_beacon_gate_submit(&g,1));
 assert(!wr_iot_beacon_gate_drained(&g,1));
 assert(!wr_iot_beacon_gate_open(&g,2));
 assert(!wr_iot_beacon_gate_end(&g,2));
 assert(wr_iot_beacon_gate_end(&g,1)); /* producer cancels */
 assert(!wr_iot_beacon_gate_end(&g,1));
 assert(wr_iot_beacon_gate_drained(&g,1));
 assert(wr_iot_beacon_gate_open(&g,2));
 assert(!wr_iot_beacon_gate_begin(&g,1));
 assert(!wr_iot_beacon_gate_drained(&g,1));
 assert(wr_iot_beacon_gate_begin(&g,2));
 assert(wr_iot_beacon_gate_end(&g,2));
 assert(wr_iot_beacon_gate_revoke(&g,2));
 assert(wr_iot_beacon_gate_drained(&g,2));
 puts("PASS beacon producer generation, close race, drain, reopen");
 return 0;
}
