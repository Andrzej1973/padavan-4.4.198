"""Add WRRB routing only after the existing privileged WPSQ route is installed."""
def compose(source):
    marker='static INT wr_iot_driver_closed_ioctl('
    target='return wr_iot_physical_rebind_ioctl(ad,dev,rq);'
    if source.count(marker)!=1 or target in source:
        raise ValueError('changed/already-routed rebind ioctl')
    start=source.index(marker);end=source.index('\n}',start)+2
    body=source[start:end]
    anchor='  return wr_iot_physical_stop_ioctl(ad,dev,rq);'
    copy=' if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;'
    guards=('if(!rtnl_is_locked())return -EBUSY;',
     'if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;',
     'if(!IS_MT7603(ad))return -EOPNOTSUPP;')
    if body.count(anchor)!=1 or body.count(copy)!=1 or body.index(copy)>body.index(anchor):
        raise ValueError('existing privileged WPSQ dispatch required')
    if any(body.count(g)!=1 or body.index(g)>body.index(copy) for g in guards):
        raise ValueError('closed ioctl guard changed')
    route="\n if(wire[0]=='W'&&wire[1]=='R'&&wire[2]=='R'&&wire[3]=='B')\n  "+target+'\n'
    declaration='static INT __attribute__((unused)) wr_iot_physical_rebind_ioctl(RTMP_ADAPTER *,PNET_DEV,struct ifreq *);\n'
    return source[:start]+declaration+body.replace(anchor,anchor+route,1)+source[end:]
