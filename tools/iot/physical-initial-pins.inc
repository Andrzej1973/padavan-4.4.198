/* Low-level detach only, not terminal acknowledgement. Caller owns RTNL,
 * outer adapter/module references and MacTabLock, and has validated exact Main
 * ARMED cancellation or COMPLETE release under transition lock. Return native
 * refs outside locks, then end lifetime, then publish durable terminal reply. */
static inline int wr_iot_physical_initial_pins_detach(
 struct wr_iot_physical_stop_pins *slot,struct wr_iot_physical_stop_pins *local,
 struct wr_iot_physical_initial_record *record,
 const struct wr_iot_physical_initial_request *request)
{
 if(!slot||!local||slot==local||local->module||local->task||local->device||
    slot->module!=1||slot->task!=current||!slot->device||
    !wr_iot_physical_initial_record_matches(record,request,current)||
    slot->device!=(struct net_device *)record->origin.main_device)return 0;
 if(request->action==WR_STOP_CANCEL){
  if(record->status!=WR_STOP_ARMED||record->completion_epoch)return 0;
 }else if(request->action==WR_STOP_RELEASE){
  if(record->status!=WR_STOP_COMPLETE||record->completion_epoch<=record->origin.epoch)return 0;
 }else return 0;
 *local=*slot;slot->module=0;slot->task=NULL;slot->device=NULL;
 /* No normal QUERY reply can treat this detached state as still owned. */
 record->task=NULL;
 return 1;
}
