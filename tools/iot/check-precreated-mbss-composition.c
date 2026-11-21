/* Compose actual reserved controller and staged admission, reusing existing
 * fixtures. Raw MBSS IO remains injected: not an end-to-end RC/driver proof. */
#define main wr_iot_mbss_post_open_fixture_main
#include "check-mbss-post-open.c"
#undef main
#define main wr_iot_activation_fixture_main
#include "check-activation.c"
#undef main

struct composed {
 struct fixture network;
 struct adapter radio;
 struct device main_dev,guest_dev,iot_dev;
 int revoke_main,bss_attempts,legacy_operations;
};
static int composed_operation(void *context,enum wr_iot_activation_operation op)
{
 struct composed *c=context;
 struct fixture *f=&c->network;
 if(op==WR_IOT_PROFILE||op==WR_IOT_RADIO_PREPARE||
    op==WR_IOT_RESTORE||op==WR_IOT_DISABLE_APPLY){
  c->legacy_operations++;return 0;
 }
 if(op==WR_IOT_RESERVED_READY){
  assert(f->locked&&!f->live);
  f->profile=f->radio_prepared=1;return 1;
 }
 if(op==WR_IOT_RESERVED_RESTORE){
  assert(f->locked&&!f->live&&!f->attached&&!f->bridge&&!f->exists);
  f->dhcp=f->policy=f->main_ready=0;return 1;
 }
 if(op==WR_IOT_BSS_UP){
  assert(f->locked&&f->guard&&f->dhcp&&f->policy);
  c->bss_attempts++;
  /* Revoke after controller MAIN_RADIO_READY, before driver admission. */
  if(c->revoke_main)wr_iot_radio_main_down(&c->radio.wr_iot_transition);
  if(MBSS_VirtualIF_Open(&c->iot_dev)!=0)return 0;
  return operation(f,op);
 }
 if(op==WR_IOT_QUIESCE&&c->radio.VirtualIfCnt>2){
  /* A raw successful open has no real retirement receipt in this fixture.
   * Do not model administrative DOWN as a sufficient RF/late-TxS boundary. */
  return 0;
 }
 return operation(f,op);
}
static void composed_unlock(void *context)
{
 struct composed *c=context;unlock(&c->network);
}
static int composed_cancel(void *context)
{
 struct composed *c=context;return cancel_requested(&c->network);
}
int main(void)
{
 /* Imported fixture also covers later publish wrappers; this composition
  * does not invoke or claim those wrappers. Keep strict unused checks. */
 (void)wr_iot_mbss_publish_ready;(void)wr_iot_mbss_publish_down;
 const struct wr_iot_activation_backend backend={
  composed_operation,composed_unlock,composed_cancel
 };
 for(int revoke=0;revoke<2;revoke++){
  struct composed c;struct wr_iot_activation state={0};
  memset(&c,0,sizeof(c));
  setup(&c.radio,&c.main_dev,&c.guest_dev,&c.iot_dev);
  assert(MBSS_VirtualIF_Open(&c.guest_dev)==0);
  assert(c.radio.VirtualIfCnt==2);
  c.revoke_main=revoke;
  int ok=wr_iot_activation_start_precreated(&state,&backend,&c);
  assert(c.bss_attempts==1&&!c.legacy_operations);
  assert(c.radio.wr_iot_interface_refs[0].phase==WR_REF_OWNED);
  assert(c.radio.wr_iot_interface_refs[1].phase==WR_REF_OWNED);
  if(revoke){
   assert(!ok&&state.state==WR_IOT_INACTIVE&&!c.network.locked);
   assert(c.radio.VirtualIfCnt==2);
   assert(c.radio.wr_iot_interface_refs[2].phase==WR_REF_IDLE);
   assert(!c.network.live&&!c.network.guard&&!c.network.dhcp);
  }else{
   assert(ok&&state.state==WR_IOT_ACTIVE&&c.network.live);
   assert(c.radio.VirtualIfCnt==3);
   assert(c.radio.wr_iot_interface_refs[2].phase==WR_REF_OWNED);
   /* Unproven retirement retains network/isolation instead of unsafe OFF. */
   assert(!wr_iot_activation_stop(&state));
   assert(state.state==WR_IOT_RECOVERY&&state.locked);
   assert(c.network.live&&c.network.guard&&c.network.dhcp&&c.network.attached);
   assert(c.radio.VirtualIfCnt==3&&!c.legacy_operations);
  }
 }
 puts("PASS composed reserved controller/MBSS admission: valid Main opens ra2; revoked Main refuses before raw mutation; unknown retirement retains isolation. Raw IO/network injected; no physical restart/scan/MCU or runtime proof.");
 return 0;
}
