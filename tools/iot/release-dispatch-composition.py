"""Route software release14 and recovery-query15 only in the complete compile-only no-host experiment."""

def compose(entry):
    copy = ' if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;'
    guards = ('if(!rtnl_is_locked())return -EBUSY;',
              'if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;',
              'if(!IS_MT7603(ad))return -EOPNOTSUPP;')
    if entry.count(copy) != 1 or 'WR_IOT_DRIVER_CLOSE_RELEASE_OPCODE' in entry:
        raise ValueError('Experimental release dispatcher boundary changed')
    if any(entry.count(guard) != 1 or entry.index(guard) > entry.index(copy)
           for guard in guards):
        raise ValueError('Experimental release privilege boundary changed')
    route = '''
 if(wire[4]==WR_IOT_IDLE_QUERY)return wr_iot_precreated_idle_reply(ad,dev,rq,wire);
 if(wire[4]==15)return wr_iot_driver_open_recovery_reply(ad,dev,rq,wire);
 if(wire[4]==WR_IOT_DRIVER_CLOSE_RELEASE_OPCODE){
  struct wr_iot_driver_close_request request;
  if(!wr_iot_driver_close_release_decode(&request,wire,sizeof(wire)))return -EINVAL;
  return wr_iot_driver_close_release(ad,dev,&request);
 }
'''
    return ('#define WR_IOT_RA2_NO_HOST_MODE 1\n'
            '#include "driver-api-close-release-wire.h"\n'
            '#include "driver-api-close-release-binding.inc"\n'
            '#include "driver-api-open-current.h"\n'
            '#include "driver-api-open-recovery-wire.h"\n'
            '#include "driver-api-open-recovery-entry.inc"\n'
            '#include "precreated-idle-wire.h"\n'
            '#include "precreated-idle-probe-binding.inc"\n'
            '#include "precreated-idle-entry.inc"\n' +
            entry.replace(copy, copy + route, 1))
