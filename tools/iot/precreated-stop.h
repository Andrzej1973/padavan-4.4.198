/* Experimental no-host driver integration. Normal OFF of an already owned ON
 * only; not startup rollback, physical radio stop or RF acceptance. Caller is
 * the serialized RC worker, outside signal context, and pins this context.
 * Do not bind production activation until its complete admission/cancel paths
 * and immutable driver mode are verified. Every failed step retains ownership. */
#ifndef WR_IOT_PRECREATED_STOP_H
#define WR_IOT_PRECREATED_STOP_H
#include "driver-close-controller.h"
#include "disable-controller.h"
#include <sys/types.h>
enum wr_iot_stop_phase {
 WR_IOT_STOP_IDLE,WR_IOT_STOP_CLOSE_BEGIN,WR_IOT_STOP_CLOSE,
 WR_IOT_STOP_ISOLATE,WR_IOT_STOP_SERVICES,WR_IOT_STOP_BRIDGE_DOWN,
 WR_IOT_STOP_DETACH,WR_IOT_STOP_REMOVE,WR_IOT_STOP_APPLY,
 WR_IOT_STOP_OBSERVE,WR_IOT_STOP_COMMIT,WR_IOT_STOP_COMPLETE,
 WR_IOT_STOP_CANCELLED
};
struct wr_iot_precreated_stop {
 struct wr_iot_driver_attempt attempt;
 struct wr_iot_close_controller close;
 struct wr_iot_disable_controller disable;
 unsigned long long close_serial;
 pid_t owner;
 int guard;
 enum wr_iot_stop_phase phase;
};
/* Zero-initialize context. Read-only snapshot/guard acquisition, no CLOSE or gate mutation. */
int wr_iot_precreated_stop_begin(struct wr_iot_precreated_stop *,
 const struct wr_iot_driver_attempt *);
/* One phase per call, no polling loop. 1 only after complete network commit;
 * 0 retains phase/identity/guard, including uncertain kernel results. */
int wr_iot_precreated_stop_step(struct wr_iot_precreated_stop *);
/* Only before any possibly submitted CLOSE; never cancels recovery after mutation. */
int wr_iot_precreated_stop_cancel(struct wr_iot_precreated_stop *);
#endif
