/* Caller holds transition lock and pins adapter/netdev. Ownership and actual
 * queued/running callbacks must both be retired before reopening main.
 * This guard alone does not authorize dropping RTNL or joining any worker. */
#ifndef WR_IOT_MAIN_REOPEN_ADMISSION_H
#define WR_IOT_MAIN_REOPEN_ADMISSION_H
#include "main-open-recovery-owner.h"
static inline int wr_iot_main_recovery_allows_reopen(
 const struct wr_iot_main_recovery_owner *owner,
 unsigned int main_work_busy,unsigned int reaper_work_busy,
 unsigned int aux_deferred_owners,unsigned int aux_work_busy)
{
 return owner&&owner->phase==WR_MAIN_OWNER_IDLE&&!owner->device&&
  !owner->generation&&!owner->open_token&&!owner->close_serial&&
  !owner->close_ticket_valid&&!owner->deferred_owners&&!owner->attempts&&
  !owner->failed_submissions&&!owner->stop_requested&&!owner->completed&&
  !owner->module_pin_released&&!owner->schedule_recorded&&
  !main_work_busy&&!reaper_work_busy&&!aux_deferred_owners&&!aux_work_busy;
}
#endif
