"""Extend reviewed Main binding with distinct never-opened origin; dormant."""
def compose(source):
    decl='  unsigned long long physical_prior_serial=0;'
    capture='   physical_prior_serial=adapter->wr_iot_physical_lifetime.arm_record_serial;'
    branch='  if (physical_armed) {\n   struct wr_iot_physical_stop_record *physical='
    if source.count(decl)!=1 or source.count(capture)!=1 or source.count(branch)!=1:
        raise ValueError('changed or duplicate initial Main binding')
    source=source.replace(decl,decl+'\n  struct wr_iot_physical_stop_lifetime initial_life={0};\n  int initial_origin=0;',1)
    source=source.replace(capture,capture+'''
   initial_origin=!physical_request.action&&!physical_prior_serial;
   if(initial_origin)initial_life=adapter->wr_iot_physical_lifetime;''',1)
    replacement='''  if (physical_armed && initial_origin) {
   struct wr_iot_physical_initial_record *initial=&adapter->wr_iot_physical_initial;
   struct wr_iot_physical_stop_pins *pins=&adapter->wr_iot_physical_pins;
   struct wr_iot_physical_initial_request initial_query;
   RTMP_IRQ_LOCK(&adapter->MacTabLock, flags);
   initial_query=initial->request;initial_query.action=WR_STOP_QUERY;
   bound=pins->module==1&&pins->task&&pins->device==net_dev&&
    initial->origin.main_device==net_dev&&
    wr_iot_physical_initial_main_binding(&initial->origin,&initial_life)&&
    wr_iot_physical_initial_record_matches(initial,&initial_query,pins->task);
   if(bound&&initial->status==WR_STOP_ARMED)
    bound=wr_iot_physical_initial_record_running(initial,&initial_query,
      pins->task,&initial_life);
   else if(bound)bound=initial->status==WR_STOP_RUNNING&&
    initial_life.main_ticket_valid&&
    initial_life.main_ticket.operation==WR_RADIO_CLOSE&&
    !initial_life.main_ticket.reset_kind&&
    initial_life.main_ticket.serial>initial->origin.idle_serial;
   RTMP_IRQ_UNLOCK(&adapter->MacTabLock, flags);
   if(!bound)goto retain;
  }
  if (physical_armed && !initial_origin) {
   struct wr_iot_physical_stop_record *physical='''
    return source.replace(branch,replacement,1)
