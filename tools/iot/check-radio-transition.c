#include "radio-transition.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 struct wr_iot_radio_transition s;struct wr_iot_radio_ticket a,b,stale;
 unsigned long old;
 /* Driver allocation is zeroed before stats/locks initialization; no
  * transition may run on that partial object. Epoch zero is never valid. */
 s=(struct wr_iot_radio_transition){0};a=(struct wr_iot_radio_ticket){0};
 for(int op=WR_RADIO_START;op<=WR_RADIO_VERIFY;op++)
  assert(!wr_iot_radio_begin(&s,0,op,&a));
 wr_iot_radio_request_close(&s);assert(!s.epoch&&!s.busy&&!s.main_ready);
 assert(!wr_iot_radio_finish(&s,&a,1));
 wr_iot_radio_transition_init(&s);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
 assert(wr_iot_radio_abort_main_open_unmutated(&s,&a));
 assert(s.phase==WR_RADIO_DOWN&&!s.main_ready&&!s.busy&&
        wr_iot_radio_ticket_retired(&s,a.serial));
 assert(!wr_iot_radio_abort_main_open_unmutated(&s,&a));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&b));
 assert(wr_iot_radio_finish(&s,&a,1)&&s.main_ready);
 /* A refusal before raw BSS mutation releases only the owned ticket. */
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));
 stale=a;stale.serial++;
 assert(!wr_iot_radio_abort_bss_open_unmutated(&s,&stale)&&s.busy);
 assert(!wr_iot_radio_ticket_retired(&s,a.serial));
 assert(wr_iot_radio_abort_bss_open_unmutated(&s,&a));
 assert(wr_iot_radio_ticket_retired(&s,a.serial));
 assert(!s.busy&&s.main_ready&&s.phase==WR_RADIO_READY);
 assert(!wr_iot_radio_abort_bss_open_unmutated(&s,&a));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));
 wr_iot_radio_request_reset(&s);
 assert(wr_iot_radio_abort_bss_open_unmutated(&s,&a));
 assert(!s.busy&&!s.main_ready&&s.reset_pending);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&a));
 assert(wr_iot_radio_finish(&s,&a,1)&&s.main_ready);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));
 wr_iot_radio_main_down(&s);
 assert(wr_iot_radio_abort_bss_open_unmutated(&s,&a));
 assert(!s.busy&&!s.main_ready&&s.main_inhibited);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_MAIN_OPEN,&a));
 assert(wr_iot_radio_finish(&s,&a,1)&&s.main_ready);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));
 wr_iot_radio_request_close(&s);
 assert(wr_iot_radio_abort_bss_open_unmutated(&s,&a));
 assert(!s.busy&&!s.main_ready&&s.phase==WR_RADIO_CLOSING);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_CLOSE,&a));
 assert(wr_iot_radio_finish(&s,&a,1)&&s.phase==WR_RADIO_DOWN);
 /* Main stop latches inhibition before waiting for an in-flight IoT open.
  * Retried teardown must not revive main readiness. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 old=s.epoch;
 assert(!wr_iot_radio_begin_main_stop(&s,0,&b));
 assert(s.epoch==old&&s.main_ready&&!s.main_inhibited);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));
 assert(!wr_iot_radio_begin_main_stop(&s,2,&b));
 assert(s.main_inhibited&&!s.main_ready&&s.busy==WR_RADIO_BSS_OPEN);
 assert(!wr_iot_radio_ticket_retired(&s,a.serial));
 old=s.epoch;
 assert(!wr_iot_radio_begin_main_stop(&s,2,&b));
 assert(s.epoch==old&&s.busy==WR_RADIO_BSS_OPEN);
 assert(wr_iot_radio_finish_unverified(&s,&a));
 assert(wr_iot_radio_ticket_retired(&s,a.serial));
 assert(!s.busy&&!s.main_ready);
 assert(wr_iot_radio_begin_main_stop(&s,2,&b));
 assert(b.operation==WR_RADIO_BSS_CLOSE);
 assert(wr_iot_radio_finish(&s,&b,1)&&!s.main_ready&&s.main_inhibited);
 assert(wr_iot_radio_ticket_retired(&s,b.serial));
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_begin_main_stop(&s,1,&b));
 assert(b.operation==WR_RADIO_CLOSE&&s.phase==WR_RADIO_CLOSING);
 assert(wr_iot_radio_finish(&s,&b,1)&&s.phase==WR_RADIO_DOWN);
 wr_iot_radio_transition_init(&s);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
 assert(wr_iot_radio_finish(&s,&a,1)&&s.main_ready);
 /* Main goes down during admitted BSS work: retain hardware state but
  * inhibit main readiness even after late success. */
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));
 old=s.epoch;wr_iot_radio_main_down(&s);
 assert(wr_iot_radio_finish(&s,&a,1)&&s.phase==WR_RADIO_READY);
 assert(s.main_inhibited&&!s.main_ready&&s.epoch!=old);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&b));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_CLOSE,&a));
 assert(wr_iot_radio_finish(&s,&a,1)&&!s.main_ready);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_MAIN_OPEN,&a));
 wr_iot_radio_main_down(&s);
 assert(wr_iot_radio_finish(&s,&a,1)&&!s.main_ready);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_MAIN_OPEN,&a));
 assert(wr_iot_radio_finish(&s,&a,1)&&s.main_ready&&!s.main_inhibited);
 old=s.epoch;
 assert(wr_iot_radio_begin(&s,old,WR_RADIO_BSS_CLOSE,&a));
 assert(!wr_iot_radio_begin(&s,old,WR_RADIO_BSS_OPEN,&b));
 assert(!wr_iot_radio_begin(&s,old,WR_RADIO_RESET,&b));
 assert(wr_iot_radio_finish(&s,&a,1));
 assert(s.phase==WR_RADIO_READY&&s.main_ready&&s.epoch==old);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));stale=a;
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&b));
 old=s.epoch;wr_iot_radio_request_close(&s);
 assert(!s.main_ready&&s.epoch!=old);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_CLOSE,&b));
 assert(wr_iot_radio_finish(&s,&a,1)&&s.phase==WR_RADIO_CLOSING&&!s.main_ready);
 assert(!wr_iot_radio_begin(&s,old,WR_RADIO_BSS_OPEN,&b));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_CLOSE,&b));
 assert(!wr_iot_radio_finish(&s,&stale,1)&&s.busy==WR_RADIO_CLOSE);
 assert(wr_iot_radio_finish(&s,&b,0)&&s.phase==WR_RADIO_CLOSING);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_CLOSE,&b));
 assert(wr_iot_radio_finish(&s,&b,1)&&s.phase==WR_RADIO_DOWN);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
 assert(wr_iot_radio_finish(&s,&a,1));
 assert(!wr_iot_radio_begin(&s,old,WR_RADIO_BSS_OPEN,&a));
 old=s.epoch;
 assert(wr_iot_radio_begin(&s,old,WR_RADIO_RESET,&a));
 assert(s.epoch!=old&&!s.main_ready);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
 assert(wr_iot_radio_finish(&s,&a,1)&&s.main_ready);
 assert(!wr_iot_radio_begin(&s,old,WR_RADIO_BSS_OPEN,&b));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&a));
 assert(wr_iot_radio_finish(&s,&a,0)&&s.phase==WR_RADIO_FAULT);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
 wr_iot_radio_request_close(&s);assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_CLOSE,&b));
 assert(wr_iot_radio_finish(&s,&b,1));
 s.epoch=~0UL;wr_iot_radio_request_close(&s);assert(s.exhausted);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_CLOSE,&b));
 assert(wr_iot_radio_finish(&s,&b,1));
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
 /* Software-open completion does not authorize BSS; actual observation
  * owns a separate exclusive ticket, and late results may only retire it. */
 for(int outcome=0;outcome<4;outcome++){
  wr_iot_radio_transition_init(&s);
  assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
  assert(wr_iot_radio_finish_unverified(&s,&a));
  assert(s.phase==WR_RADIO_UNVERIFIED&&!s.main_ready);
  assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
  assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_VERIFY,&a));
  assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&b));
  if(outcome==1)wr_iot_radio_main_down(&s);
  if(outcome==2)wr_iot_radio_request_close(&s);
  assert(wr_iot_radio_verify_finish(&s,&a,outcome!=3)==(outcome==0));
  assert(!s.busy);
  if(outcome==0){
   assert(s.main_ready&&wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
  }else{
   assert(!s.main_ready&&!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
  }
 }
 /* Reset requested during an observation must survive late observation
  * completion; repeated requests coalesce and cannot starve via new opens. */
 wr_iot_radio_transition_init(&s);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
 assert(wr_iot_radio_finish_unverified(&s,&a));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_VERIFY,&a));
 wr_iot_radio_request_reset(&s);old=s.epoch;
 wr_iot_radio_request_reset(&s);assert(s.epoch==old&&s.reset_pending);
 assert(!wr_iot_radio_verify_finish(&s,&a,1)&&!s.busy&&!s.main_ready);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_MAIN_OPEN,&a));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&a)&&!s.reset_pending);
 wr_iot_radio_request_reset(&s);assert(s.reset_pending);
 assert(wr_iot_radio_finish(&s,&a,1)&&!s.main_ready&&s.reset_pending);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&a));
 assert(wr_iot_radio_finish_unverified(&s,&a)&&!s.reset_pending&&!s.main_ready);
 wr_iot_radio_request_reset(&s);wr_iot_radio_request_close(&s);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_CLOSE,&a));
 assert(wr_iot_radio_finish(&s,&a,1)&&!s.reset_pending);
 /* A first START is still phase DOWN while hardware work is in flight:
  * reset requests must not disappear just because startup is incomplete. */
 wr_iot_radio_transition_init(&s);
 assert(!wr_iot_radio_request_reset_kind(&s,WR_RADIO_RESET_PSE));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
 assert(wr_iot_radio_request_reset_kind(&s,WR_RADIO_RESET_PDMA));old=s.epoch;
 assert(wr_iot_radio_request_reset_kind(&s,WR_RADIO_RESET_PSE)&&s.epoch==old);
 assert(s.reset_pending==(WR_RADIO_RESET_PDMA|WR_RADIO_RESET_PSE));
 assert(!wr_iot_radio_request_reset_kind(&s,4)&&s.epoch==old);
 assert(wr_iot_radio_finish_unverified(&s,&a)&&s.reset_pending);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&a));
 assert(a.reset_kind==(WR_RADIO_RESET_PDMA|WR_RADIO_RESET_PSE));
 assert(wr_iot_radio_request_reset_kind(&s,WR_RADIO_RESET_PDMA));
 assert(wr_iot_radio_finish_unverified(&s,&a));
 assert(s.reset_pending==WR_RADIO_RESET_PDMA);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&a)&&a.reset_kind==WR_RADIO_RESET_PDMA);
 assert(wr_iot_radio_finish_unverified(&s,&a)&&!s.reset_pending);
 /* Selective teardown must remain possible after unverified/failed open,
  * but may never upgrade that baseline to verified READY. */
 for(int state=0;state<3;state++){
  wr_iot_radio_transition_init(&s);
  s.phase=state==0?WR_RADIO_READY:state==1?WR_RADIO_UNVERIFIED:WR_RADIO_FAULT;
  s.main_ready=state==0;
  assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_CLOSE,&a));
  assert(wr_iot_radio_finish(&s,&a,1));
  assert(s.phase==(state==0?WR_RADIO_READY:state==1?WR_RADIO_UNVERIFIED:WR_RADIO_FAULT));
  assert(s.main_ready==(state==0));
 }
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_UNVERIFIED;
 wr_iot_radio_request_reset_kind(&s,WR_RADIO_RESET_PSE);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_CLOSE,&a));
 assert(wr_iot_radio_finish(&s,&a,1));
 assert(s.phase==WR_RADIO_UNVERIFIED&&!s.main_ready&&s.reset_pending);
 /* Stop classification uses a caller-stabilized count, never decrements it. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 old=s.epoch;
 assert(!wr_iot_radio_begin_stop(&s,0,&a));
 assert(s.epoch==old&&s.phase==WR_RADIO_READY&&s.main_ready&&!s.busy);
 assert(wr_iot_radio_begin_stop(&s,2,&a)&&a.operation==WR_RADIO_BSS_CLOSE);
 assert(wr_iot_radio_finish(&s,&a,1)&&s.phase==WR_RADIO_READY&&s.main_ready);
 assert(wr_iot_radio_begin_stop(&s,1,&a)&&a.operation==WR_RADIO_CLOSE);
 assert(s.phase==WR_RADIO_CLOSING&&!s.main_ready);
 assert(wr_iot_radio_finish(&s,&a,1)&&s.phase==WR_RADIO_DOWN);
 /* Last-stop intent survives refusal while previously admitted work retires. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));
 assert(!wr_iot_radio_begin_stop(&s,1,&b));old=s.epoch;
 assert(s.phase==WR_RADIO_CLOSING&&!s.main_ready&&s.busy);
 assert(!wr_iot_radio_begin_stop(&s,1,&b)&&s.epoch==old);
 assert(wr_iot_radio_finish_unverified(&s,&a)&&!s.busy&&!s.main_ready);
 assert(wr_iot_radio_begin_stop(&s,1,&b)&&b.operation==WR_RADIO_CLOSE);
 assert(wr_iot_radio_finish(&s,&b,1)&&s.phase==WR_RADIO_DOWN);
 /* Removal blocks fresh work while allowing mandatory family teardown. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));
 wr_iot_radio_retire(&s);old=s.epoch;wr_iot_radio_retire(&s);
 assert(s.retiring&&s.epoch==old&&!s.main_ready);
 assert(wr_iot_radio_finish_unverified(&s,&a)&&!s.main_ready);
 assert(!wr_iot_radio_request_reset_kind(&s,WR_RADIO_RESET_PSE));
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_VERIFY,&a));
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_MAIN_OPEN,&a));
 assert(wr_iot_radio_begin_stop(&s,2,&a));
 assert(wr_iot_radio_finish(&s,&a,1)&&!s.main_ready&&s.retiring);
 assert(wr_iot_radio_begin_stop(&s,1,&a));
 assert(wr_iot_radio_finish(&s,&a,1)&&s.phase==WR_RADIO_DOWN&&s.retiring);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
 /* A suspend racing an admitted reset invalidates completion, retains the
  * reset bit through PCI-off, and reopens only into UNVERIFIED recovery. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_request_reset_kind(&s,WR_RADIO_RESET_PSE));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&a));
 assert(!s.reset_pending&&a.reset_kind==WR_RADIO_RESET_PSE);
 old=s.epoch;assert(wr_iot_radio_request_suspend(&s));
 assert(s.phase==WR_RADIO_SUSPENDING&&s.epoch!=old&&!s.main_ready);
 assert(s.reset_pending==WR_RADIO_RESET_PSE);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
 assert(!wr_iot_radio_suspend_complete(&s));
 assert(!wr_iot_radio_resume_unverified(&s));
 assert(wr_iot_radio_finish(&s,&a,1));
 assert(!s.busy&&s.phase==WR_RADIO_SUSPENDING&&!s.main_ready);
 assert(s.reset_pending==WR_RADIO_RESET_PSE);
 assert(wr_iot_radio_suspend_complete(&s));
 assert(s.phase==WR_RADIO_SUSPENDED&&s.pm_suspended&&!s.pm_suspending);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&b));
 assert(wr_iot_radio_request_reset_kind(&s,WR_RADIO_RESET_PDMA));
 assert(s.reset_pending==(WR_RADIO_RESET_PSE|WR_RADIO_RESET_PDMA));
 assert(wr_iot_radio_resume_unverified(&s));
 assert(s.phase==WR_RADIO_UNVERIFIED&&!s.pm_suspended&&!s.main_ready);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&a));
 assert(a.reset_kind==(WR_RADIO_RESET_PSE|WR_RADIO_RESET_PDMA)&&!s.reset_pending);
 assert(wr_iot_radio_finish(&s,&a,1)&&s.phase==WR_RADIO_READY&&s.main_ready);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
 /* Closing during suspend may retire the radio, but cannot erase reset
  * intent; PCI-off is not proof that resume recovery has completed. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 wr_iot_radio_request_reset_kind(&s,WR_RADIO_RESET_PDMA);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&a));
 assert(wr_iot_radio_request_suspend(&s));
 wr_iot_radio_request_close(&s);
 assert(wr_iot_radio_finish(&s,&a,1));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_CLOSE,&b));
 assert(wr_iot_radio_finish(&s,&b,1));
 assert(s.phase==WR_RADIO_DOWN&&s.reset_pending==WR_RADIO_RESET_PDMA);
 assert(wr_iot_radio_suspend_complete(&s));
 assert(wr_iot_radio_resume_unverified(&s));
 assert(s.phase==WR_RADIO_UNVERIFIED&&s.reset_pending==WR_RADIO_RESET_PDMA);
 assert(!s.busy&&s.reset_pending==WR_RADIO_RESET_PDMA&&!s.main_ready);
 /* A late successful BSS-open cannot publish readiness across suspend. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));
 assert(wr_iot_radio_request_suspend(&s));
 assert(wr_iot_radio_finish(&s,&a,1));
 assert(s.phase==WR_RADIO_SUSPENDING&&!s.main_ready&&!s.busy);
 assert(wr_iot_radio_suspend_complete(&s));
 assert(wr_iot_radio_resume_unverified(&s));
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_MAIN_OPEN,&a));
 assert(wr_iot_radio_finish_unverified(&s,&a)&&!s.main_ready);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_VERIFY,&a));
 assert(wr_iot_radio_verify_finish(&s,&a,1)&&s.main_ready);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
 /* PCI suspend may race the first START while the public phase is still DOWN. */
 wr_iot_radio_transition_init(&s);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
 assert(s.phase==WR_RADIO_DOWN&&s.busy==WR_RADIO_START);
 assert(wr_iot_radio_request_suspend(&s));
 assert(wr_iot_radio_finish(&s,&a,1)&&s.phase==WR_RADIO_SUSPENDING&&!s.main_ready);
 assert(wr_iot_radio_suspend_complete(&s));
 assert(wr_iot_radio_resume_unverified(&s));
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_VERIFY,&a));
 assert(wr_iot_radio_verify_finish(&s,&a,1)&&s.main_ready);
 /* The PM fence refuses new TX but cannot complete until two admitted
  * transmit calls have both returned from the driver entry. */
 assert(wr_iot_radio_tx_enter(&s));
 assert(wr_iot_radio_tx_enter(&s)&&s.active_tx==2);
 assert(wr_iot_radio_request_suspend(&s));
 assert(!wr_iot_radio_tx_enter(&s));
 assert(!wr_iot_radio_suspend_complete(&s));
 assert(!wr_iot_radio_tx_leave(&s)&&s.active_tx==1);
 assert(!wr_iot_radio_suspend_complete(&s));
 assert(wr_iot_radio_tx_leave(&s)&&!s.active_tx);
 assert(!wr_iot_radio_tx_leave(&s));
 assert(wr_iot_radio_suspend_complete(&s));
 assert(!wr_iot_radio_tx_enter(&s));
 assert(wr_iot_radio_resume_unverified(&s));
 assert(!wr_iot_radio_tx_enter(&s));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_VERIFY,&a));
 assert(wr_iot_radio_verify_finish(&s,&a,1));
 assert(wr_iot_radio_tx_enter(&s));
 wr_iot_radio_request_close(&s);
 assert(!wr_iot_radio_tx_enter(&s));
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_CLOSE,&a));
 assert(wr_iot_radio_tx_leave(&s));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_CLOSE,&a));
 assert(wr_iot_radio_finish(&s,&a,1));
 /* Reset intent closes TX admission before waiting for an in-flight call. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_tx_enter(&s));
 assert(wr_iot_radio_request_reset_kind(&s,WR_RADIO_RESET_PDMA));
 assert(!wr_iot_radio_tx_enter(&s));
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&a));
 assert(wr_iot_radio_tx_leave(&s));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_RESET,&a));
 assert(wr_iot_radio_finish(&s,&a,1));
 /* A failed pre-close PM attempt releases the PM marker but cannot reopen TX
  * or BSS admission until independent verification. Preserve reset intent. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_tx_enter(&s));
 assert(wr_iot_radio_request_suspend(&s));
 assert(wr_iot_radio_abort_suspend(&s));
 assert(s.phase==WR_RADIO_UNVERIFIED&&!s.pm_suspending&&!s.main_ready);
 assert(!wr_iot_radio_tx_enter(&s));
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_VERIFY,&a));
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_MAIN_OPEN,&a));
 assert(wr_iot_radio_tx_leave(&s));
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_VERIFY,&a));
 assert(wr_iot_radio_verify_finish(&s,&a,1));
 assert(!wr_iot_radio_abort_suspend(&s));
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_request_suspend(&s));
 assert(wr_iot_radio_request_reset_kind(&s,WR_RADIO_RESET_PDMA));
 assert(wr_iot_radio_abort_suspend(&s));
 assert(s.reset_pending==WR_RADIO_RESET_PDMA&&s.phase==WR_RADIO_UNVERIFIED);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&a));
 /* A pre-mutation PM timeout may restore READY while the old TX continues.
  * The caller must prove it has not detached queues or changed vendor flags. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_tx_enter(&s));
 assert(wr_iot_radio_request_suspend(&s));
 assert(wr_iot_radio_abort_suspend_unmutated(&s));
 assert(s.phase==WR_RADIO_READY&&s.main_ready&&!s.pm_suspending&&s.active_tx==1);
 assert(wr_iot_radio_tx_enter(&s));
 assert(!wr_iot_radio_tx_leave(&s));
 assert(wr_iot_radio_tx_leave(&s));
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_request_suspend(&s));
 assert(wr_iot_radio_request_reset_kind(&s,WR_RADIO_RESET_PDMA));
 assert(!wr_iot_radio_abort_suspend_unmutated(&s));
 assert(wr_iot_radio_abort_suspend(&s));
 assert(s.phase==WR_RADIO_UNVERIFIED&&s.reset_pending==WR_RADIO_RESET_PDMA);
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_UNVERIFIED;
 assert(wr_iot_radio_request_suspend(&s));
 assert(!wr_iot_radio_abort_suspend_unmutated(&s));
 assert(wr_iot_radio_abort_suspend(&s));
 /* Failed physical close leaves CLOSING. It cannot complete suspend, but
  * after the owning ticket retires it can abort into UNVERIFIED. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_request_suspend(&s));
 wr_iot_radio_request_close(&s);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_CLOSE,&a));
 assert(!wr_iot_radio_abort_suspend(&s));
 assert(wr_iot_radio_finish(&s,&a,0));
 assert(s.phase==WR_RADIO_CLOSING&&!s.busy);
 assert(!wr_iot_radio_suspend_complete(&s));
 assert(wr_iot_radio_abort_suspend(&s));
 assert(s.phase==WR_RADIO_UNVERIFIED&&!s.pm_suspending&&!s.main_ready);
 assert(!wr_iot_radio_begin(&s,s.epoch,WR_RADIO_BSS_OPEN,&b));
 /* If close completed but a later PCI action fails, abort still does not
  * claim radio readiness or permit another BSS open. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_request_suspend(&s));
 wr_iot_radio_request_close(&s);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_CLOSE,&a));
 assert(wr_iot_radio_finish(&s,&a,1)&&s.phase==WR_RADIO_DOWN);
 assert(wr_iot_radio_abort_suspend(&s));
 assert(s.phase==WR_RADIO_UNVERIFIED&&!s.main_ready);
 /* An auxiliary vendor success may arrive after a reset/main-down request.
  * Ticket retirement alone must not publish the netdevice as owned. */
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_begin_aux_open(&s,1,&a));
 assert(wr_iot_radio_finish(&s,&a,1));
 assert(wr_iot_aux_open_accepted(&s,&a,1));
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_begin_aux_open(&s,1,&a));
 wr_iot_radio_request_reset(&s);
 assert(wr_iot_radio_finish(&s,&a,1));
 assert(!wr_iot_aux_open_accepted(&s,&a,1));
 wr_iot_radio_transition_init(&s);s.phase=WR_RADIO_READY;s.main_ready=1;
 assert(wr_iot_radio_begin_aux_open(&s,1,&a));
 wr_iot_radio_request_close(&s);
 assert(wr_iot_radio_finish(&s,&a,1));
 assert(!wr_iot_aux_open_accepted(&s,&a,1));
 /* Main success is intentionally UNVERIFIED until readback, but a late
  * success after reset or close must retain uncertain ownership. */
 wr_iot_radio_transition_init(&s);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
 assert(wr_iot_radio_finish_unverified(&s,&a));
 assert(wr_iot_main_open_accepted(&s,&a,1));
 wr_iot_radio_transition_init(&s);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
 wr_iot_radio_request_reset(&s);
 assert(wr_iot_radio_finish_unverified(&s,&a));
 assert(!wr_iot_main_open_accepted(&s,&a,1));
 wr_iot_radio_transition_init(&s);
 assert(wr_iot_radio_begin(&s,s.epoch,WR_RADIO_START,&a));
 wr_iot_radio_request_close(&s);
 assert(wr_iot_radio_finish_unverified(&s,&a));
 assert(!wr_iot_main_open_accepted(&s,&a,1));
 puts("PASS radio admission: exclusive tickets, TX drain gates, close/reset interleavings, fail-closed suspend/resume/abort and verified BSS recovery; sequential model only, PM/driver integration pending");
 return 0;
}
