"""Route WPSQ through existing Linux CLOSED_CONFIG ioctl in isolated no-host tree.

No new ioctl number or firmware protocol. Wrapper repeats authorization/identity
and fully validates its own copied request, so a changed userspace buffer cannot
bypass the physical transaction boundary.
"""
def compose(source):
    marker='static INT wr_iot_driver_closed_ioctl('
    if source.count(marker)!=1 or 'return wr_iot_physical_stop_ioctl(ad,dev,rq);' in source:
        raise ValueError('changed/already-routed closed ioctl')
    start=source.index(marker);end=source.index('\n}',start)+2
    body=source[start:end]
    copy=' if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;'
    guards=('if(!rtnl_is_locked())return -EBUSY;',
            'if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;',
            'if(!IS_MT7603(ad))return -EOPNOTSUPP;')
    if body.count(copy)!=1 or any(body.count(g)!=1 or body.index(g)>body.index(copy) for g in guards):
        raise ValueError('closed ioctl privilege/copy boundary changed')
    route='''
 if(wire[0]=='W'&&wire[1]=='P'&&wire[2]=='S'&&wire[3]=='Q')
  return wr_iot_physical_stop_ioctl(ad,dev,rq);
'''
    declaration='static INT __attribute__((unused)) wr_iot_physical_stop_ioctl(RTMP_ADAPTER *,PNET_DEV,struct ifreq *);\n'
    return source[:start]+declaration+body.replace(copy,copy+route,1)+source[end:]
