#define _GNU_SOURCE
#include <unistd.h>
#include "cold-on-scheduler.h"
#include "cold-on-root.h"
/* All child pointers refer into this single stable, noncopied PID1 slot. */
static struct wr_iot_cold_root cold_scheduler;
int wr_iot_rc_cold_on_begin(const struct wr_iot_control_request *request,int reload)
{return wr_iot_cold_root_begin(&cold_scheduler,request,reload);}
int wr_iot_cold_on_pending(void)
{return cold_scheduler.owner!=0;}
int wr_iot_cold_on_step(void)
{
 if(cold_scheduler.owner!=getpid())return 0;
 return wr_iot_cold_root_step(&cold_scheduler);
}
int wr_iot_cold_on_retire(void)
{return wr_iot_cold_root_retire(&cold_scheduler);}
