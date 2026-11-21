/* Internal request only. Caller pins adapter/netdev. No waits under this lock.
 * Table emptiness is checked atomically with reservation, not supplied by OS. */
static INT wr_iot_peer_open_dispatch(RTMP_ADAPTER *pAd,
 struct wr_iot_peer_open_request *request,ULONG size)
{
 struct wr_iot_peer_open_ticket ticket;
 UINT i;
 INT accepted=0;
 if (!pAd || !request || size!=sizeof(*request) ||
     request->version!=WR_IOT_PEER_OPEN_REQUEST_VERSION ||
     !request->device) return NDIS_STATUS_FAILURE;
 ticket.device=request->device;ticket.serial=request->serial;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if (request->device!=pAd->net_dev) goto done;
 switch(request->action) {
 case WR_PEER_OPEN_CONFIG_CHECK:
  accepted=wr_iot_peer_open_matches(&pAd->wr_iot_peer_open_owner,
   &pAd->wr_iot_peer_table_owner,&ticket) &&
   pAd->wr_iot_peer_open_owner.phase==WR_PEER_OPEN_CONFIG;break;
 case WR_PEER_OPEN_BEGIN:
  if (request->serial || pAd->MacTab.Size) break;
  /* Unpublished failed entries may not be represented by Size/hash. */
  for(i=1;i<MAX_LEN_OF_MAC_TABLE;i++)
   if (!IS_ENTRY_NONE(&pAd->MacTab.Content[i])) goto done;
  for(i=1;i<MAX_LEN_OF_TR_TABLE;i++)
   if (pAd->MacTab.tr_entry[i].wr_iot_setup_observed &&
       pAd->MacTab.tr_entry[i].wr_iot_setup_result!=0) goto done;
  accepted=wr_iot_peer_open_begin(&pAd->wr_iot_peer_open_owner,
   &pAd->wr_iot_peer_table_owner,request->device,1,&ticket);
  if(accepted)request->serial=ticket.serial;
  break;
 case WR_PEER_OPEN_START:
  accepted=wr_iot_peer_open_startup(&pAd->wr_iot_peer_open_owner,
   &pAd->wr_iot_peer_table_owner,&ticket);break;
 case WR_PEER_OPEN_DONE:
 case WR_PEER_OPEN_FAIL:
  accepted=wr_iot_peer_open_finish(&pAd->wr_iot_peer_open_owner,
   &pAd->wr_iot_peer_table_owner,&ticket,request->action==WR_PEER_OPEN_DONE);break;
 default:break;
 }
done:
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return accepted ? NDIS_STATUS_SUCCESS : NDIS_STATUS_FAILURE;
}
