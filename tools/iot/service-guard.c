#define _GNU_SOURCE
#include <string.h>
#include "service-lock.h"
#include "service-guard.h"
#ifndef WR_IOT_SERVICE_LOCK_PATH
#define WR_IOT_SERVICE_LOCK_PATH "/var/run/wr-iot-services.lock"
#endif
static struct wr_iot_service_lock held={-1};
static unsigned int depth;
static pid_t owner;
int wr_iot_service_guard_enter(int enabled){
 pid_t current=getpid();
 if(owner&&owner!=current){wr_iot_service_lock_release(&held);depth=0;}
 owner=current;
 if(depth){
  if(depth>=32||!wr_iot_service_lock_valid(&held,WR_IOT_SERVICE_LOCK_PATH))return 0;
  depth++;return 1;
 }
 if(!enabled)return 2;
 if(!wr_iot_service_lock_take(&held,WR_IOT_SERVICE_LOCK_PATH))return 0;
 depth=1;return 1;
}
void wr_iot_service_guard_leave(int token){
 if(token!=1||owner!=getpid()||!depth)return;
 if(!--depth)wr_iot_service_lock_release(&held);
}
