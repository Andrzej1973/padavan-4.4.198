/* Private nonsecret baseline for a configuration-only RC operation. The
 * backend retains its existing runtime owner and loaded credential proof. */
#ifndef WR_IOT_CONFIG_BACKEND_H
#define WR_IOT_CONFIG_BACKEND_H
enum wr_iot_config_backend_kind {
 WR_IOT_CONFIG_BACKEND_NONE=0,WR_IOT_CONFIG_BACKEND_IDLE,
 WR_IOT_CONFIG_BACKEND_REBIND_ACTIVE,WR_IOT_CONFIG_BACKEND_ACTIVE,
 WR_IOT_CONFIG_BACKEND_REBIND_OFF,WR_IOT_CONFIG_BACKEND_OFF,
 WR_IOT_CONFIG_BACKEND_INITIAL_OFF
};
struct wr_iot_config_backend {
 enum wr_iot_config_backend_kind kind;char id[33];unsigned long long created;
};
/* Caller retains service guard and one shutdown admission. ACTIVE requires
 * an already armed and available normal-shutdown route. These functions never
 * execute activation, change radio/profile state or acquire that route. */
int wr_iot_rc_config_backend_capture(struct wr_iot_config_backend *);
int wr_iot_rc_config_backend_current(const struct wr_iot_config_backend *);
#endif
