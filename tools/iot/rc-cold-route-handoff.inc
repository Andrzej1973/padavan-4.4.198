/* Private cold followup handoff, after cold followup and root declarations.
 * No physical completion or service-success claim. A routed signal continues
 * to exclude ordinary admission after this exact nonsecret root retirement. */
static int cold_routed_iapp_released(const struct wr_iot_terminal_iapp *t,
 const struct wr_iot_iapp_child *child)
{
 if(t->busy||t->guard||t->fence.owner||t->fence.level||t->child||
    t->shutdown_held||!wr_iot_iapp_child_closed(child))return 0;
 if(!t->owner)return !t->attempted&&!t->result&&!child->owner&&!child->fd;
 return t->owner==getpid()&&t->result==-1&&
  (child->owner?t->attempted&&child->result==-1:!child->fd);
}

static int cold_disabled_routed_ready(const struct wr_iot_cold_root *s)
{
 const struct wr_iot_cold_disabled_terminal *t=&s->disabled_terminal;
 const struct wr_iot_cold_disabled_release *r=&s->disabled_release;
 if(s->release.owner||s->terminal.owner||s->disabled.owner||
    !s->disabled_released.released||s->disabled_released.busy||
    s->disabled_released.release!=r||(r->wan.attempted&&!r->wan.returned)||
    t->busy||!cold_routed_iapp_released(&t->terminal,&t->child))return 0;
 if(s->phase==WR_COLD_ROOT_TERMINAL_BEGIN)
  return !t->owner&&!t->parent_release&&t->phase==WR_COLD_DISABLED_TERM_IDLE;
 return t->owner==getpid()&&t->parent_release==&s->disabled_released&&
  (t->phase==WR_COLD_DISABLED_TERM_WAN||t->phase==WR_COLD_DISABLED_TERM_IAPP_PENDING||t->phase==WR_COLD_DISABLED_TERM_RETAINED);
}

static int cold_routed_root_handoff(struct wr_iot_cold_root *s)
{
 struct wr_iot_cold_terminal *t;int guard,ok=0;
 if(!s||s->owner!=getpid()||s->busy||(s->enabled!=0&&s->enabled!=1)||
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
    s->final_off_attempted||s->final_off.owner)return 0;
 if(!s->enabled){
  if(!cold_disabled_routed_ready(s))return 0;
 }else{
  if(s->disabled.owner||s->disabled_release.owner||s->disabled_terminal.owner||
     (s->release.wan.attempted&&!s->release.wan.returned)||
     !s->released.released||s->released.busy||s->released.release!=&s->release)return 0;
  t=&s->terminal;
  /* Never abandon a child or an inherited terminal fence. Existing IAPP must
   * drain through its established owned shutdown path, separately integrated. */
  if(t->busy||!cold_routed_iapp_released(&t->terminal,&t->child)||
     (t->owner&&t->owner!=getpid())||
     (t->owner&&(t->parent_release!=&s->released||
       (t->phase!=WR_COLD_TERM_WAN&&t->phase!=WR_COLD_TERM_IAPP_PENDING&&t->phase!=WR_COLD_TERM_RETAINED))))return 0;
 }
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(!wr_iot_rc_normal_shutdown_cold_handoff_ready()||
    !(s->enabled?wr_iot_cold_followup_active(&s->release):
                 wr_iot_cold_disabled_followup_current(&s->disabled_release))||
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
