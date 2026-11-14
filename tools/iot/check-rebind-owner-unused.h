/* Legacy-only backend fixtures must never enter a rebind owner. */
#include "rebind-owner.h"
int wr_iot_rebind_owner_begin(struct wr_iot_rebind_owner*s,const struct wr_iot_control_request*r,const struct wr_iot_physical_stop_request*p,int a,int b,int c){(void)s;(void)r;(void)p;(void)a;(void)b;(void)c;assert(0);return 0;}
enum wr_iot_result_state wr_iot_rebind_owner_execute(struct wr_iot_rebind_owner*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return WR_IOT_RESULT_RECOVERY;}
enum wr_iot_result_state wr_iot_rebind_owner_continue(struct wr_iot_rebind_owner*s,const char*i,unsigned long long c){(void)s;(void)i;(void)c;assert(0);return WR_IOT_RESULT_RECOVERY;}
int wr_iot_rebind_owner_observed(const struct wr_iot_rebind_owner*s,const struct wr_iot_control_result*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_rebind_owner_closed(const struct wr_iot_rebind_owner*s,const struct wr_iot_control_result*r,struct wr_iot_driver_closed_result*c){(void)s;(void)r;(void)c;assert(0);return 0;}
