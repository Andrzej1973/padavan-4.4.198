#include "radio-transition.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
 struct wr_iot_radio_transition s;
 struct wr_iot_radio_ticket t, stale;
 unsigned long epoch;

 wr_iot_radio_transition_init(&s);
 assert(!wr_iot_radio_begin(&s, s.epoch, WR_RADIO_AUX_OPEN, &t));
 s.main_inhibited=1;
 assert(wr_iot_radio_begin_aux_open(&s, 0, &t));
 assert(t.operation==WR_RADIO_AUX_START);
 assert(wr_iot_radio_abort_aux_open_unmutated(&s, &t));
 assert(s.phase==WR_RADIO_DOWN&&!s.main_ready&&s.main_inhibited);
 assert(wr_iot_radio_begin_aux_open(&s, 0, &t));
 assert(wr_iot_radio_finish(&s, &t, 1));
 assert(s.phase==WR_RADIO_READY&&!s.main_ready&&s.main_inhibited);
 assert(!wr_iot_radio_begin(&s, s.epoch, WR_RADIO_BSS_OPEN, &stale));
 assert(wr_iot_radio_begin_aux_open(&s, 1, &t));
 assert(t.operation==WR_RADIO_AUX_OPEN);
 assert(wr_iot_radio_finish(&s, &t, 1));
 assert(!s.main_ready&&s.main_inhibited);
 assert(wr_iot_radio_begin(&s, s.epoch, WR_RADIO_MAIN_OPEN, &t));
 assert(wr_iot_radio_finish(&s, &t, 1));
 assert(s.main_ready&&!s.main_inhibited);
 assert(wr_iot_radio_begin(&s, s.epoch, WR_RADIO_AUX_OPEN, &t));
 assert(!wr_iot_radio_begin(&s, s.epoch, WR_RADIO_BSS_OPEN, &stale));
 stale=t;stale.serial++;
 assert(!wr_iot_radio_abort_aux_open_unmutated(&s, &stale));
 assert(wr_iot_radio_abort_aux_open_unmutated(&s, &t));
 assert(!s.busy&&s.phase==WR_RADIO_READY&&s.main_ready);
 assert(wr_iot_radio_begin(&s, s.epoch, WR_RADIO_AUX_OPEN, &t));
 assert(wr_iot_radio_finish(&s, &t, 1));
 assert(wr_iot_radio_begin_aux_stop(&s, 2, &t));
 assert(t.operation==WR_RADIO_AUX_CLOSE);
 assert(wr_iot_radio_finish(&s, &t, 1));
 assert(s.phase==WR_RADIO_READY&&s.main_ready);

 assert(wr_iot_radio_begin(&s, s.epoch, WR_RADIO_AUX_OPEN, &t));
 epoch=s.epoch;
 wr_iot_radio_request_reset(&s);
 assert(wr_iot_radio_abort_aux_open_unmutated(&s, &t));
 assert(!s.busy&&s.reset_pending&&s.epoch!=epoch);
 assert(!wr_iot_radio_begin(&s, s.epoch, WR_RADIO_AUX_OPEN, &t));
 assert(wr_iot_radio_begin(&s, s.epoch, WR_RADIO_RESET, &t));
 assert(wr_iot_radio_finish(&s, &t, 1));
 assert(wr_iot_radio_begin_aux_stop(&s, 1, &t));
 assert(t.operation==WR_RADIO_CLOSE&&s.phase==WR_RADIO_CLOSING);
 assert(wr_iot_radio_finish(&s, &t, 0));
 assert(s.phase==WR_RADIO_CLOSING&&!s.main_ready);
 /* A late successful physical start cannot override a queued reset. */
 wr_iot_radio_transition_init(&s);
 assert(wr_iot_radio_begin_aux_open(&s, 0, &t));
 epoch=s.epoch;
 wr_iot_radio_request_reset(&s);
 assert(s.reset_pending&&s.epoch!=epoch);
 assert(wr_iot_radio_finish(&s, &t, 1));
 assert(s.phase==WR_RADIO_UNVERIFIED&&!s.main_ready&&s.reset_pending);
 /* Main-down during start also invalidates the ticket's readiness proof. */
 wr_iot_radio_transition_init(&s);
 assert(wr_iot_radio_begin_aux_open(&s, 0, &t));
 wr_iot_radio_main_down(&s);
 assert(wr_iot_radio_finish(&s, &t, 1));
 assert(s.phase==WR_RADIO_UNVERIFIED&&!s.main_ready&&s.main_inhibited);
 assert(!wr_iot_radio_begin_aux_open(&s, 1, &t));
 /* The same rule applies to a later auxiliary open on an active radio. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_begin_aux_open(&s, 1, &t));
 wr_iot_radio_request_reset(&s);
 assert(wr_iot_radio_finish(&s, &t, 1));
 assert(s.phase==WR_RADIO_UNVERIFIED&&!s.main_ready&&s.reset_pending);
 puts("PASS auxiliary radio tickets: distinct open/close, reset fence and failed last close");
 return 0;
}
