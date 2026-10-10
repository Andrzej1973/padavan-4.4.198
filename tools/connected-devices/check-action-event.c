#include "action-event.h"
#include <assert.h>
#include <stdio.h>
int main(void){struct wr_action_event e={0};e.session=1;e.sequence=1;e.mac[0]=2;e.source=WR_ACTION_RSSI;e.stage=WR_ACTION_INTENT;assert(wr_action_valid(&e));
 e.stage=WR_ACTION_FRAME_SUBMITTED;assert(wr_action_valid(&e));e.stage=WR_ACTION_IOCTL_ACCEPTED;assert(!wr_action_valid(&e));
 e.source=WR_ACTION_STEERING;assert(wr_action_valid(&e));e.stage=WR_ACTION_ENTRY_REMOVED;assert(!wr_action_valid(&e));e.stage=WR_ACTION_DRIVER_ACK;e.radio=2;assert(!wr_action_valid(&e));e.radio=0;e.mac[0]=1;assert(!wr_action_valid(&e));e.mac[0]=2;e.sequence=0;assert(!wr_action_valid(&e));
 puts("PASS separate steering/RSSI stages and bounded event identity; transport authentication not verified");return 0;}
