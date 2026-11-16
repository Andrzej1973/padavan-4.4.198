#include "rc-normal-shutdown.h"
/* Include after rc-cold-start.inc, only inside the private RC backend.
 * Prepared experimental runtime detaches a reference only;
 * the ACTIVE initial runner and its own stop/rollback state remain intact.
 * Caller owns outer admission/fence and serialization throughout. */
static int wr_iot_cold_detach_preflight(const struct wr_iot_cold_owner *parent,
 const struct wr_iot_control_request *request)
{
 return parent&&request&&!wr_iot_rc_shutdown.radio_on_owned&&
  wr_iot_rc_cold_active_current(parent,request)&&
  wr_iot_rc_normal_shutdown_cold_arm_ready();
}
/* Infallible callback primitive after preflight, used only within successful
 * outer fence cleanup. Do not call while unmask can still fail. No credential,
 * profile, guard, exclusion or backend-owner mutation is performed here. */
static void wr_iot_cold_detach_commit(void)
{
 wr_iot_cold_backend_parent=NULL;
 memset(&wr_iot_cold_backend_identity,0,sizeof(wr_iot_cold_backend_identity));
}
