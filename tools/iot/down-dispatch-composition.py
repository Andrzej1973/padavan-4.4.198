"""Optional compile-only DOWN route after existing privileged single copy-in."""
def compose(entry):
    binding='#include "precreated-down-binding.inc"\n'
    anchor=' if(wire[4]==WR_IOT_IDLE_QUERY)return wr_iot_precreated_idle_reply(ad,dev,rq,wire);'
    copy=' if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;'
    guards=('if(!rtnl_is_locked())return -EBUSY;',
            'if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;')
    if entry.count(binding)!=1 or entry.count(anchor)!=1 or entry.count(copy)!=1 or 'WR_IOT_DOWN_QUERY' in entry:
        raise ValueError('DOWN common entry boundary changed')
    if any(entry.count(g)!=1 or entry.index(g)>entry.index(copy) for g in guards):
        raise ValueError('DOWN privilege boundary changed')
    route='''
 if(wire[4]==WR_IOT_DOWN_QUERY){
  int down_status=wr_iot_precreated_down_reply(ad,dev,wire,sizeof(wire),wire);
  if(down_status)return down_status;
  return copy_to_user(rq->ifr_data,wire,sizeof(wire))?-EFAULT:0;
 }
'''
    # The reply calls static functions defined by the binding. Prefixing it
    # before the complete entry creates implicit/external declarations first.
    entry=entry.replace(binding,binding+'#include "precreated-down-reply.inc"\n',1)
    return entry.replace(anchor,route+anchor,1)
