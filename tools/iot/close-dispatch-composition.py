"""Route existing CLOSE operations after common capability and fixed-copy checks."""
def compose(entry):
    anchor = ' if(wire[4]==8)return wr_iot_driver_uncertain_reply(ad,dev,rq,wire);'
    copy = ' if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;'
    guards = ['if(!rtnl_is_locked())return -EBUSY;',
              'if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;',
              'if(!IS_MT7603(ad))return -EOPNOTSUPP;']
    if entry.count(anchor) != 1 or entry.count(copy) != 1:
        raise ValueError('CLOSE common dispatch/copy anchor changed')
    if 'return wr_iot_driver_close_reply(' in entry:
        raise ValueError('CLOSE dispatch already installed')
    if any(entry.count(g) != 1 or entry.index(g) > entry.index(copy) for g in guards):
        raise ValueError('CLOSE common privilege boundary changed')
    if entry.index(copy) > entry.index(anchor):
        raise ValueError('CLOSE fixed copy must precede dispatch')
    routes = ''' if(wire[4]==WR_IOT_DRIVER_CLOSE_REQUEST_OPCODE||
    wire[4]==WR_IOT_DRIVER_CLOSE_PROGRESS_OPCODE){
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  matched=ad->ApCfg.BssidNum==3&&ad->net_dev!=dev&&
   ad->ApCfg.MBSSID[2].wdev.if_dev==dev;
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  if(!matched)return -EBUSY;
  if(wire[4]==WR_IOT_DRIVER_CLOSE_REQUEST_OPCODE)
   return wr_iot_driver_close_reply(ad,dev,rq,wire);
  return wr_iot_driver_close_progress_reply(ad,dev,wire);
 }
'''
    return entry.replace(anchor, routes + anchor, 1)
