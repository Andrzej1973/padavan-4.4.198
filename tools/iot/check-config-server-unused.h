/* Runtime-only fixtures deliberately exclude configuration execution and its
 * observer. The real shared-server/config-owner composition opts out of these
 * actors and links config-server.c and its actual private owner. */
#ifndef WR_IOT_CHECK_CONFIG_SERVER_UNUSED_H
#define WR_IOT_CHECK_CONFIG_SERVER_UNUSED_H
#include "control-record.h"
#include <assert.h>
#ifndef WR_IOT_TEST_CONFIG_SERVER_REAL
enum wr_iot_result_state wr_iot_rc_config_execute(const struct wr_iot_control_request *r)
{(void)r;assert(0);return WR_IOT_RESULT_RECOVERY;}
enum wr_iot_result_state wr_iot_rc_config_continue(const char *id,unsigned long long created)
{(void)id;(void)created;assert(0);return WR_IOT_RESULT_RECOVERY;}
int wr_iot_rc_config_terminal_ready(const struct wr_iot_control_result *r)
{(void)r;assert(0);return 0;}
int wr_iot_rc_config_observed(const struct wr_iot_control_result *r)
{(void)r;assert(0);return 0;}
int wr_iot_configuration_result_observed(const struct wr_iot_control_result *r)
{(void)r;assert(0);return 0;}
#endif
#endif
