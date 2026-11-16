/* Private cold followup handoff, after cold followup and root declarations.
 * No physical completion or service-success claim. A routed signal continues
 * to exclude ordinary admission after this exact nonsecret root retirement. */
static int cold_routed_root_handoff(struct wr_iot_cold_root *s)
{
 struct wr_iot_cold_terminal *t;int guard,ok=0;
 if(!s||s->owner!=getpid()||s->busy||s->enabled!=1||
    (s->phase!=WR_COLD_ROOT_TERMINAL_BEGIN&&s->phase!=WR_COLD_ROOT_TERMINAL)||
    !wr_iot_rc_shutdown.normal_route_armed||
    (wr_iot_rc_shutdown.normal_route_requested!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.normal_route_requested!=SIGQUIT
#endif
    )||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned!=1||wr_iot_rc_shutdown.radio_off_owned||
    s->parent.owner||s->parent.generation.owner||s->parent.main.owner||
    s->parent.guest.owner||s->parent.services.owner||s->parent.multicast.owner||
    s->parent.admission.guard||s->parent.admission.fence.owner||
    s->parent.admission.profile.files.count||s->handoff.owner||s->stop.owner||
    s->final_off_attempted||s->final_off.owner||s->disabled.owner||
    s->disabled_release.owner||s->disabled_terminal.owner||
    !s->released.released||s->released.busy||s->released.release!=&s->release)return 0;
 t=&s->terminal;
 /* Never abandon a child or an inherited terminal fence. Existing IAPP must
  * drain through its established owned shutdown path, separately integrated. */
 if(t->busy||t->terminal.owner||t->terminal.busy||t->terminal.guard||
    t->terminal.fence.owner||t->terminal.fence.level||t->terminal.child||
    t->terminal.attempted||t->child.owner||t->child.attempted||
    (t->owner&&t->owner!=getpid())||
    (t->owner&&(t->parent_release!=&s->released||
      (t->phase!=WR_COLD_TERM_WAN&&t->phase!=WR_COLD_TERM_IAPP_PENDING))))return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(!wr_iot_rc_normal_shutdown_cold_handoff_ready()||
    !wr_iot_cold_followup_active(&s->release)||
    !wr_iot_rc_normal_shutdown_cold_handoff_ready())goto done;
 /* Route remains armed/requested; no other PID1 process-context writer can
  * acquire this root. Do not represent skipped IAPP as DONE or successful. */
 {volatile unsigned char *p=(volatile unsigned char*)s;size_t n=sizeof(*s);
  while(n--)*p++=0;}
 wr_iot_rc_shutdown.radio_on_owned=0;ok=1;
 done:wr_iot_service_guard_leave(guard);return ok;
}

int wr_iot_rc_cold_root_routed_handoff(struct wr_iot_cold_root *s)
{return cold_routed_root_handoff(s);}
