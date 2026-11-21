"""Read-only OPEN receipt route behind the existing privilege/copy boundary."""
def compose(closed):
 anchor=' if(wire[4]==8)return wr_iot_driver_uncertain_reply(ad,dev,rq,wire);'
 if closed.count(anchor)!=1 or 'wr_iot_driver_open_current_reply' in closed:
  raise ValueError('Current OPEN observation dispatch anchor changed')
 copy=' if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;'
 if closed.count(copy)!=1 or closed.index(copy)>closed.index(anchor):raise ValueError('User copy boundary changed')
 for guard in ['if(!rtnl_is_locked())return -EBUSY;','if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;']:
  if closed.count(guard)!=1 or closed.index(guard)>closed.index(copy):raise ValueError('Privilege boundary changed')
 closed=closed.replace(anchor,' if(wire[4]==11)return wr_iot_driver_open_current_reply(ad,dev,rq,wire);\n'+anchor,1)
 return '#include "driver-api-open-current.h"\n#include "driver-api-open-current-entry.inc"\n'+closed
