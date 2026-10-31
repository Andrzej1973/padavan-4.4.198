/* Begin only; this neither closes children nor proves callback retirement. */
static int wr_iot_pci_children_begin(RTMP_ADAPTER *adapter)
{
 ULONG flags;UINT i;unsigned int expected=0;int result=0;
 if(!adapter)return 0;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 if(!adapter->wr_iot_transition.retiring || adapter->wr_iot_registration_inflight ||
    adapter->wr_iot_pci_retirement.phase!=WR_PCI_RETIRE_WORK_JOINED)goto done;
 for(i=0;i<WDEV_NUM_MAX+1;i++){
  const struct wr_iot_interface_ref *r=&adapter->wr_iot_interface_refs[i];
  if(!r->device){
   if(r->published||r->removing||r->phase!=WR_REF_IDLE)goto done;
   continue;
  }
  if(!r->generation||!r->published)goto done;
  switch(r->family){
  case WR_REF_FAMILY_MAIN:break;
  case WR_REF_FAMILY_APCLI:expected|=WR_CHILD_APCLI;break;
  case WR_REF_FAMILY_WDS:expected|=WR_CHILD_WDS;break;
  case WR_REF_FAMILY_MBSS:expected|=WR_CHILD_MBSS;break;
  case WR_REF_FAMILY_MONITOR:expected|=WR_CHILD_MONITOR;break;
  default:goto done;
  }
 }
 result=wr_child_teardown_begin(&adapter->wr_iot_children,expected,1);
done:
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);return result;
}
