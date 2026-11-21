/* Staged Linux binding. Common ioctl owns RTNL and pins adapter/registration
 * throughout entry. Successful reservation installs the existing active-owner
 * adapter fence, plus a distinct netdev/module hold retained across dev_close.
 * These are EXTRA holds, not the original open's module ownership. No release
 * is allowed on reference-only completion. The isolated candidate dispatcher
 * uses the checked retirement and recovery ownership-transfer bindings. */
static INT wr_iot_driver_close_request_enter(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_driver_close_request *request,const void *task)
{
 ULONG flags=0;int accepted=0;
 if(!ad||!dev||!request||!task||task!=current)return -EINVAL;
 if(request->adapter_epoch!=(unsigned long)request->adapter_epoch||
    request->device_generation!=(unsigned long)request->device_generation||
    request->open_token!=(unsigned long)request->open_token)return -EINVAL;
 if(!try_module_get(THIS_MODULE))return -ENODEV;
 dev_hold(dev);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(IS_MT7603(ad)&&ad->ApCfg.BssidNum==3&&ad->net_dev!=dev&&
    ad->ApCfg.MBSSID[2].wdev.if_dev==dev){
  accepted=wr_iot_driver_close_reserve(&ad->wr_iot_close_owner,
   &ad->wr_iot_driver_owner,request->open_request_id,&ad->wr_iot_transition,
   ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,ad->net_dev,dev,task,
   (unsigned long)request->adapter_epoch,(unsigned long)request->device_generation,
   (unsigned long)request->open_token,VIRTUAL_IF_NUM(ad),ad->wr_iot_control_users,
   ad->wr_iot_control_poisoned||ad->wr_iot_boot_active||ad->wr_iot_boot_failed,
   ad->wr_iot_closed_probe.active);
  if(accepted){ad->wr_iot_close_owner.netdev_held=1;ad->wr_iot_close_owner.module_held=1;}
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!accepted){dev_put(dev);module_put(THIS_MODULE);}
 return accepted?0:-EBUSY;
}
