#include "rc-shutdown-admission.h"
#include <assert.h>
#include <stdio.h>

struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;

int main(void){
 assert(!wr_iot_rc_shutdown_note(SIGTERM));
 assert(wr_iot_rc_shutdown_begin());
 assert(!wr_iot_rc_shutdown_begin());
 assert(!wr_iot_rc_shutdown_note(SIGSEGV));
#ifdef SIGPWR
 assert(!wr_iot_rc_shutdown_note(SIGPWR));
#endif
 assert(wr_iot_rc_shutdown_note(SIGTERM));
#ifdef SIGQUIT
 assert(wr_iot_rc_shutdown_note(SIGQUIT));
#endif
 assert(wr_iot_rc_shutdown.pending==SIGTERM);
 assert(!wr_iot_rc_shutdown_begin());
 assert(wr_iot_rc_shutdown_end()==SIGTERM);
 assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);
 assert(wr_iot_rc_shutdown_begin());
 assert(wr_iot_rc_shutdown_end()==0);
 puts("PASS IoT RC shutdown admission: normal signal deferred; fault signal remains immediate; host model only");
 return 0;
}
