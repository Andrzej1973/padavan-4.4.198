#ifndef WR_IOT_RC_BOOT_H
#define WR_IOT_RC_BOOT_H
/* Arm only after the paired init_router() returns. No work in the arm hook. */
void wr_iot_rc_boot_arm(void);
int wr_iot_rc_boot_pending(void);
/* Bounded readiness poll, no radio restart.1 published a new initial queue
 * request; caller dispatches later through the canonical mailbox owner. */
int wr_iot_rc_boot_step(void);
#endif
