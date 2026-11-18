/* Counterexample only: counted control lifetime is not key-writer exclusion. */
#include <assert.h>
#include <stdio.h>
typedef unsigned long ULONG;
typedef int INT32;
typedef void VOID;
typedef struct {
 unsigned int wr_iot_control_users,wr_iot_control_poisoned;
 unsigned int wr_iot_boot_active,wr_iot_boot_failed;
 unsigned int wr_iot_ra2_key_active;
 int wr_iot_transition_lock;
 struct {unsigned int busy,retiring,reset_pending,pm_suspending,pm_suspended;} wr_iot_transition;
} RTMP_ADAPTER;
#define RTMP_IRQ_LOCK(lock,flags) do{(void)(lock);(void)(flags);}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) RTMP_IRQ_LOCK(lock,flags)
#include "mcu-control-admission.inc"
int main(void)
{
 RTMP_ADAPTER ad={0};
 /* Existing GTK actor owns its reference and exclusive key flag. A generic
  * control caller can still enter; a separate scoped mutation guard is needed
  * for a reachable ioctl writer. No driver operation or MMIO is simulated. */
 ad.wr_iot_ra2_key_active=1;ad.wr_iot_control_users=1;
 assert(wr_iot_control_enter(&ad));
 assert(ad.wr_iot_control_users==2&&ad.wr_iot_ra2_key_active==1);
 wr_iot_control_leave(&ad);
 assert(ad.wr_iot_control_users==1&&ad.wr_iot_ra2_key_active==1);
 ad.wr_iot_transition.busy=1;
 assert(!wr_iot_control_enter(&ad)&&ad.wr_iot_control_users==1);
 puts("CONFIRMED GAP: control lifetime admission alone does not exclude active ra2 key writer; no runtime race claim");
 return 0;
}
