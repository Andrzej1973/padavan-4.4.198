#include "start-network.h"
#include "driver-open-controller.h"
#include "start-commit.h"
int wr_iot_start_network_step(struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_request*r,const unsigned char*i){(void)n;(void)a;(void)r;(void)i;assert(0);return 0;}
int wr_iot_open_controller_submit(struct wr_iot_open_controller*s,const char*i,const struct wr_iot_request*r){(void)s;(void)i;(void)r;assert(0);return 0;}
int wr_iot_start_commit_step(struct wr_iot_start_commit*c,struct wr_iot_start_admission*a,const struct wr_iot_start_network*n,const struct wr_iot_open_controller*o,const struct wr_iot_request*r){(void)c;(void)a;(void)n;(void)o;(void)r;assert(0);return 0;}
int wr_iot_open_controller_recovery_read(const struct wr_iot_open_controller*s,struct wr_iot_driver_open_recovery_result*r){(void)s;(void)r;assert(0);return 0;}
