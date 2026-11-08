/* Isolated candidate compilation bundle. No ioctl route is installed here.
 * Keep the same dependency order in the standalone target probe. */
#ifndef WR_IOT_DRIVER_CLOSE_BUNDLE_H
#define WR_IOT_DRIVER_CLOSE_BUNDLE_H
#include <linux/module.h>
#include <linux/kthread.h>
#include <linux/sched.h>
#include <linux/rtnetlink.h>
#include "driver-api-close-finish.h"
#include "driver-api-close-recovery.h"
#include "driver-api-close-progress-match.h"
#include "driver-api-close-enter.inc"
#include "driver-api-close-finish-binding.inc"
#include "driver-api-close-recovery-binding.inc"
#include "driver-api-close-synchronous-put.h"
#include "driver-api-close-synchronous-put.inc"
#include "driver-api-close-finish-recovery.inc"
#include "driver-api-close-entry.inc"
#include "driver-api-close-retirement.h"
#include "driver-api-close-retirement-binding.inc"
#include "driver-api-close-retirement-create.inc"
#include "driver-api-close-retirement-cancel.inc"
#include "driver-api-close-retirement-start.inc"
#include "driver-api-close-retirement-thread-entry.inc"
#include "driver-api-close-retirement-thread-body.inc"
#include "driver-api-close-retirement-launch.inc"
#include "driver-api-close-retirement-reconcile.inc"
#include "driver-api-close-progress.inc"
#include "driver-api-close-progress-wire.h"
#include "driver-api-close-progress-entry.inc"
#include "driver-api-close-progress-ioctl.inc"
#endif
