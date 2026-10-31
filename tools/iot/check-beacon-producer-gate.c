#include "beacon-producer-gate.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
 struct wr_iot_beacon_producer_gate g;
 struct wr_iot_beacon_producer_ticket first={0},second={0},stale={0};
 wr_iot_beacon_gate_init(&g);
 assert(!wr_iot_beacon_gate_begin(&g,1,&first));
 assert(!wr_iot_beacon_gate_open(&g,0));
 assert(wr_iot_beacon_gate_open(&g,1));
 assert(wr_iot_beacon_gate_begin(&g,1,&first)); /* pointer acquired */
 assert(!wr_iot_beacon_gate_begin(&g,1,&first));
 assert(wr_iot_beacon_gate_begin(&g,1,&second));
 assert(wr_iot_beacon_gate_submit(&g,&first));
 assert(wr_iot_beacon_gate_revoke(&g,1)); /* close races with preparation */
 assert(wr_iot_beacon_gate_revoke(&g,1)); /* retained close retries */
 assert(!wr_iot_beacon_gate_revoke(&g,2));
 assert(!wr_iot_beacon_gate_begin(&g,1,&stale));
 assert(!wr_iot_beacon_gate_submit(&g,&first));
 assert(!wr_iot_beacon_gate_drained(&g,1));
 assert(!wr_iot_beacon_gate_open(&g,2));
 assert(wr_iot_beacon_gate_end(&g,&first)); /* producer cancels */
 assert(!wr_iot_beacon_gate_end(&g,&first));
 assert(!wr_iot_beacon_gate_drained(&g,1));
 assert(wr_iot_beacon_gate_end(&g,&second));
 assert(wr_iot_beacon_gate_drained(&g,1));
 assert(wr_iot_beacon_gate_open(&g,2));
 assert(!wr_iot_beacon_gate_end(&g,&first));
 assert(!wr_iot_beacon_gate_begin(&g,1,&stale));
 assert(!wr_iot_beacon_gate_drained(&g,1));
 assert(wr_iot_beacon_gate_begin(&g,2,&stale));
 assert(!wr_iot_beacon_gate_submit(&g,&first));
 assert(wr_iot_beacon_gate_end(&g,&stale));
 assert(wr_iot_beacon_gate_revoke(&g,2));
 assert(wr_iot_beacon_gate_drained(&g,2));
 puts("PASS beacon producer generation, close race, drain, reopen");
 return 0;
}
