/* Core/NETIF caller transport. No private adapter-layout access in OS module.
 * request is kernel-owned stack storage and caller pins device/adapter. */
static INT wr_iot_peer_open_call(VOID *adapter,struct wr_iot_peer_open_request *request,UINT action)
{
 struct wr_iot_peer_open_request copy;
 INT result;
 if(!adapter||!request)return NDIS_STATUS_FAILURE;
 copy=*request;copy.action=action;
 result=RTMP_COM_IoctlHandle(adapter,NULL,CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER,0,&copy,sizeof(copy));
 if(result==NDIS_STATUS_SUCCESS && action==WR_PEER_OPEN_BEGIN)request->serial=copy.serial;
 return result;
}
static INT wr_iot_peer_open_release_config(VOID *adapter,struct wr_iot_peer_open_request *request)
{
 if(wr_iot_peer_open_call(adapter,request,WR_PEER_OPEN_START)!=NDIS_STATUS_SUCCESS)
  return NDIS_STATUS_FAILURE;
 return wr_iot_peer_open_call(adapter,request,WR_PEER_OPEN_DONE);
}
