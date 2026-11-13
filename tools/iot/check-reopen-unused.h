/* Initial-only fixtures: every reopen adapter must stay unreachable. */
#include "reopen-start.h"
#include "reopen-network.h"
#include "reopen-rollback.h"
int wr_iot_reopen_start_begin(struct wr_iot_start_admission *a,const struct wr_iot_reopen_witness *w){(void)a;(void)w;assert(0);return 0;}
int wr_iot_reopen_start_stage(struct wr_iot_start_admission*a,const struct wr_iot_reopen_witness*w,const char*(*r)(void*,const char*),void*c,int x,int y,int z){(void)a;(void)w;(void)r;(void)c;(void)x;(void)y;(void)z;assert(0);return 0;}
int wr_iot_reopen_network_step(struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_request*r,const struct wr_iot_reopen_witness*w){(void)n;(void)a;(void)r;(void)w;assert(0);return 0;}
int wr_iot_reopen_rollback_step(struct wr_iot_start_network_rollback*b,struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_open_controller*o,const struct wr_iot_reopen_witness*w){(void)b;(void)n;(void)a;(void)o;(void)w;assert(0);return 0;}
int wr_iot_reopen_witness_current(const struct wr_iot_reopen_witness*w){(void)w;assert(0);return 0;}

#include "reopen-admission.h"
int wr_iot_reopen_witness_take(struct wr_iot_reopen_witness*w,const struct wr_iot_start_runner*a,const struct wr_iot_active_stop*s){(void)w;(void)a;(void)s;assert(0);return 0;}
int wr_iot_reopen_recovered_witness_take(struct wr_iot_reopen_witness*w,const struct wr_iot_start_runner*a){(void)w;(void)a;assert(0);return 0;}
