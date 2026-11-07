/* Reuse the existing network/owner fault fixture, not a second controller. */
#define main wr_iot_legacy_fixture_main
#include "check-activation.c"
#undef main
static unsigned reserved_ready,reserved_restore,reserved_remove,forbidden;
static int reserved_operation(void *context,enum wr_iot_activation_operation op){
 struct fixture *f=context;
 if(op==WR_IOT_PROFILE||op==WR_IOT_RADIO_PREPARE||op==WR_IOT_RESTORE||op==WR_IOT_DISABLE_APPLY){forbidden++;assert(0);}
 if(op==WR_IOT_RESERVED_READY){
  assert(f->locked&&!f->live);
  reserved_ready++;
  if(f->fail==(int)op+1){f->fail=0;return 0;}
  /* Injected receipt: no driver readback or physical radio operation here. */
  f->profile=f->radio_prepared=1;return 1;
 }
 if(op==WR_IOT_RESERVED_RESTORE){
  assert(f->locked&&!f->live&&!f->attached&&!f->bridge&&!f->exists);
  if(f->recovery_fail==(int)op+1)return 0;
  f->dhcp=f->policy=f->main_ready=0;reserved_restore++;return 1;
 }
 if(op==WR_IOT_RESERVED_DISABLE_APPLY){
  assert(f->locked&&!f->live&&f->guard&&!f->exists&&!f->attached&&f->stop_snapshot);
  assert(f->main_config==f->stop_config);
  if(f->recovery_fail==(int)op+1)return 0;
  f->dhcp=f->policy=0;reserved_remove++;return 1;
 }
 return operation(context,op);
}
int main(void){
 const struct wr_iot_activation_backend b={reserved_operation,unlock,cancel_requested};
 struct wr_iot_activation s={0};struct fixture f={0};
 for(unsigned n=0;n<100;n++){
  assert(wr_iot_activation_start_precreated(&s,&b,&f));
  assert(s.state==WR_IOT_ACTIVE&&s.precreated&&f.live&&f.guard&&f.dhcp);
  f.main_config=1000+(int)n;
  assert(wr_iot_activation_stop(&s));
  assert(s.state==WR_IOT_INACTIVE&&!f.live&&!f.locked&&f.profile&&f.radio_prepared);
  assert(f.main_config==1000+(int)n);
 }
 assert(reserved_ready==100&&reserved_remove==100&&!reserved_restore&&!forbidden);
 const enum wr_iot_activation_operation failures[]={WR_IOT_QUIESCE,WR_IOT_RESERVED_READY,WR_IOT_BRIDGE_PREPARE,WR_IOT_ISOLATE,WR_IOT_ATTACH,WR_IOT_BRIDGE_UP,WR_IOT_DHCP_START,WR_IOT_POLICY,WR_IOT_MAIN_RADIO_READY,WR_IOT_BSS_UP,WR_IOT_OBSERVE};
 for(unsigned n=0;n<sizeof(failures)/sizeof(failures[0]);n++){
  memset(&s,0,sizeof(s));memset(&f,0,sizeof(f));f.fail=failures[n]+1;
  assert(!wr_iot_activation_start_precreated(&s,&b,&f));
  assert(s.state==WR_IOT_INACTIVE&&!s.locked&&!f.live&&!f.locked&&!f.guard);
 }
 /* Unknown/preprovision mismatch refuses without fallback and retains a
  * failed scoped rollback for retry, never a global profile restore. */
 memset(&s,0,sizeof(s));memset(&f,0,sizeof(f));
 f.fail=WR_IOT_RESERVED_READY+1;f.recovery_fail=WR_IOT_RESERVED_RESTORE+1;
 assert(!wr_iot_activation_start_precreated(&s,&b,&f));
 assert(s.state==WR_IOT_RECOVERY&&s.locked&&s.precreated);
 f.recovery_fail=0;assert(wr_iot_activation_stop(&s));
 /* Stop partial failure keeps BSS closed and reservations intact. */
 memset(&s,0,sizeof(s));memset(&f,0,sizeof(f));
 assert(wr_iot_activation_start_precreated(&s,&b,&f));
 f.recovery_fail=WR_IOT_RESERVED_DISABLE_APPLY+1;
 assert(!wr_iot_activation_stop(&s));assert(!f.live&&s.locked&&s.precreated&&f.profile);
 f.recovery_fail=0;assert(wr_iot_activation_stop(&s));
 /* Every OFF failure retains its transaction for retry. In particular a
  * failed quiescence must not detach an interface that might still transmit;
  * later failures must never reopen it or regenerate the radio profile. */
 const enum wr_iot_activation_operation stop_failures[]={
  WR_IOT_QUIESCE,WR_IOT_ISOLATE,WR_IOT_DISABLE_SERVICES,
  WR_IOT_BRIDGE_DOWN,WR_IOT_DETACH,WR_IOT_BRIDGE_REMOVE,
  WR_IOT_RESERVED_DISABLE_APPLY,WR_IOT_DISABLE_OBSERVE,
  WR_IOT_GUARD_REMOVE,WR_IOT_DISABLE_COMMIT
 };
 for(unsigned n=0;n<sizeof(stop_failures)/sizeof(stop_failures[0]);n++){
  memset(&s,0,sizeof(s));memset(&f,0,sizeof(f));
  assert(wr_iot_activation_start_precreated(&s,&b,&f));
  unsigned opens=(unsigned)f.bss_open_calls;
  f.main_config=2000+(int)n;
  f.recovery_fail=stop_failures[n]+1;
  assert(!wr_iot_activation_stop(&s));
  assert(s.state==WR_IOT_RECOVERY&&s.locked&&s.snapshot&&s.precreated&&s.disabling);
  assert(f.locked&&f.stop_snapshot&&f.profile&&f.radio_prepared);
  assert(f.main_config==2000+(int)n&&(unsigned)f.bss_open_calls==opens&&!forbidden);
  if(stop_failures[n]==WR_IOT_QUIESCE)
   assert(f.live&&f.attached&&f.bridge&&f.guard&&f.dhcp);
  else assert(!f.live);
  /* The same fault is persistent: a second attempt cannot release ownership. */
  assert(!wr_iot_activation_stop(&s));
  assert(s.state==WR_IOT_RECOVERY&&s.locked&&f.locked&&f.profile);
  f.recovery_fail=0;
  assert(wr_iot_activation_stop(&s));
  assert(s.state==WR_IOT_INACTIVE&&!s.locked&&!s.snapshot&&!s.disabling);
  assert(!f.live&&!f.attached&&!f.bridge&&!f.exists&&!f.guard&&!f.dhcp&&!f.stop_snapshot);
  assert(f.profile&&f.radio_prepared&&f.main_config==2000+(int)n);
  assert((unsigned)f.bss_open_calls==opens&&!forbidden);
 }
 assert(!forbidden);
 puts("PASS precreated activation:100 cycles, all11 start-stage and all10 stop-stage failures with persistent-fault retry, loaded-profile refusal, retained rollback, no legacy profile/reload/restore dispatch. Injected backend; loaded identity and hardware pending.");return 0;
}
