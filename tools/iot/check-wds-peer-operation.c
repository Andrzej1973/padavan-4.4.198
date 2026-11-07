#include <assert.h>
#include <stddef.h>
#include "wds-peer-operation.h"
int main(void){struct wr_iot_wds_peer_operation s;int dev,other;
wr_iot_wds_peer_operation_init(&s,&dev,1);
assert(wr_iot_wds_peer_operation_enter(&s,&dev,1));
assert(wr_iot_wds_peer_operation_enter(&s,&dev,1)&&s.active==2);
assert(!wr_iot_wds_peer_operation_begin_remove(&s,&dev,1)&&!s.removing);
assert(!wr_iot_wds_peer_operation_leave(&s,&dev,2)&&s.active==2);
assert(!wr_iot_wds_peer_operation_leave(&s,&other,1)&&s.active==2);
assert(wr_iot_wds_peer_operation_leave(&s,&dev,1));
assert(wr_iot_wds_peer_operation_leave(&s,&dev,1)&&!s.active);
assert(!wr_iot_wds_peer_operation_leave(&s,&dev,1));
assert(wr_iot_wds_peer_operation_begin_remove(&s,&dev,1));
assert(!wr_iot_wds_peer_operation_enter(&s,&dev,1));
assert(!wr_iot_wds_peer_operation_begin_remove(&s,&dev,1));
wr_iot_wds_peer_operation_init(&s,&dev,2);s.active=~0U;
assert(!wr_iot_wds_peer_operation_enter(&s,&dev,2)&&s.active==~0U);
assert(!wr_iot_wds_peer_operation_enter(NULL,&dev,2));return 0;}
