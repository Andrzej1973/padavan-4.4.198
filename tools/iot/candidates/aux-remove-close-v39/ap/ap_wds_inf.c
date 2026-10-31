
/*
 ***************************************************************************
 * Ralink Tech Inc.
 * 4F, No. 2 Technology 5th Rd.
 * Science-based Industrial Park
 * Hsin-chu, Taiwan, R.O.C.
 *
 * (c) Copyright 2002, Ralink Technology, Inc.
 *
 * All rights reserved. Ralink's source code is an unpublished work and the
 * use of a copyright notice does not imply otherwise. This source code
 * contains confidential trade secret material of Ralink Tech. Any attemp
 * or participation in deciphering, decoding, reverse engineering or in any
 * way altering the source code is stricitly prohibited, unless the prior
 * written consent of Ralink Technology, Inc. is obtained.
 ***************************************************************************

    Module Name:
    ap_wds.c

    Abstract:
    Support WDS function.

    Revision History:
    Who       When            What
    ------    ----------      ----------------------------------------------
    Fonchi    02-13-2007      created
*/
#define RTMP_MODULE_OS

#ifdef WDS_SUPPORT

#include "rt_config.h"
#include "virtual-open-claim.h"
#include "aux-close-claim.h"
#include "rtmp_comm.h"
#include "rt_os_util.h"
#include "rt_os_net.h"


NET_DEV_STATS *RT28xx_get_wds_ether_stats(PNET_DEV net_dev);


/* Register WDS interface */
VOID RT28xx_WDS_Init(VOID *pAd, PNET_DEV net_dev)
{
	RTMP_OS_NETDEV_OP_HOOK netDevOpHook;

	NdisZeroMemory((PUCHAR)&netDevOpHook, sizeof(RTMP_OS_NETDEV_OP_HOOK));
	netDevOpHook.open = WdsVirtualIF_open;
	netDevOpHook.stop = WdsVirtualIF_close;
	netDevOpHook.xmit = rt28xx_send_packets;
	netDevOpHook.ioctl = rt28xx_ioctl;
	netDevOpHook.get_stats = RT28xx_get_wds_ether_stats;
	NdisMoveMemory(&netDevOpHook.devAddr[0], RTMP_OS_NETDEV_GET_PHYADDR(net_dev), MAC_ADDR_LEN);
	DBGPRINT(RT_DEBUG_TRACE, ("The new WDS interface MAC = %02X:%02X:%02X:%02X:%02X:%02X\n", 
				PRINT_MAC(netDevOpHook.devAddr)));

	RTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_WDS_INIT,
						0, &netDevOpHook, 0);
	
}


INT WdsVirtualIF_open(PNET_DEV dev)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record;
 unsigned long generation=0;
 ULONG flags;
 int admitted,up,finished,ready,owned,retain_pin=1;
 if(!dev)return -1;
 RT_MOD_INC_USE_COUNT();
 adapter=RTMP_OS_NETDEV_GET_PRIV(dev);
 if(!adapter){RT_MOD_DEC_USE_COUNT();return -1;}
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 /* WDS may not become the first physical radio owner until its separate
  * first-open recovery path exists. The main interface normally owns it. */
 admitted=VIRTUAL_IF_NUM(adapter)>0 &&
  wr_iot_aux_open_reserve(&adapter->wr_iot_transition,
   adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,WR_REF_FAMILY_WDS,
   VIRTUAL_IF_NUM(adapter),&ticket,&generation);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!admitted){RT_MOD_DEC_USE_COUNT();return -1;}
 up=VIRTUAL_IF_UP_CLAIM(adapter,dev,&ticket,generation)==0;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find(adapter->wr_iot_interface_refs,
                            WDEV_NUM_MAX+1,dev,generation);
 finished=wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,up);
 ready=wr_iot_aux_open_accepted(&adapter->wr_iot_transition,&ticket,finished);
 owned=ready&&up&&record&&
  wr_iot_ref_complete_aux_open(record,dev,generation,ticket.serial,
                               0,1,1,0,0,&retain_pin);
 if(!owned&&record&&record->phase==WR_REF_RESERVED)
  wr_iot_ref_complete_aux_open(record,dev,generation,ticket.serial,
                               0,1,up&&ready,0,0,&retain_pin);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 wake_up_all(&adapter->wr_iot_ticket_wait);
 /* After a virtual-UP attempt, retain the module pin on any uncertain
  * outcome. Failed ndo_open has no guaranteed ndo_stop callback. */
 if(!owned)return -1;
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 RT_MOD_HNAT_REG(dev);
#endif
 RTMP_OS_NETDEV_START_QUEUE(dev);
 return 0;
}

INT WdsVirtualIF_close(PNET_DEV dev)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record;
 unsigned long generation=0;
 ULONG flags;
 int admitted,ret,consumed=0;
 if(!dev)return -1;
 adapter=RTMP_OS_NETDEV_GET_PRIV(dev);
 if(!adapter)return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 admitted=wr_iot_aux_close_reserve(&adapter->wr_iot_transition,
  adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,WR_REF_FAMILY_WDS,
  VIRTUAL_IF_NUM(adapter),&ticket,&generation);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!admitted)return -1; /* retain pin; last-close needs physical owner */

 RTMP_OS_NETDEV_STOP_QUEUE(dev);
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 RT_MOD_HNAT_DEREG(dev);
#endif
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find(adapter->wr_iot_interface_refs,
                            WDEV_NUM_MAX+1,dev,generation);
 if(!record||record->phase!=WR_REF_CLOSING||
    record->close_serial!=ticket.serial||
    adapter->wr_iot_transition.busy!=WR_RADIO_AUX_CLOSE||
    adapter->wr_iot_transition.serial!=ticket.serial){
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
  return -1; /* owner must reconcile prior queue/HNAT effects */
 }
 record->close_stage=1;
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);

 ret=wr_iot_virtual_down_checked(adapter,&ticket);
 if(ret!=NDIS_STATUS_SUCCESS)return -1; /* retain ticket, record and pin */
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 consumed=wr_iot_aux_close_finalize_after_down(&adapter->wr_iot_transition,
  adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation,&ticket,1,
  VIRTUAL_IF_NUM(adapter));
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!consumed)return -1; /* no safe replay without checked recovery owner */
 wake_up_all(&adapter->wr_iot_ticket_wait);
 RT_MOD_DEC_USE_COUNT();
 return 0;
}

/* Called only by a future retained recovery owner with a netdev/adapter pin.
 * It cannot be scheduled from ndo_stop until worker teardown is implemented. */
INT WdsVirtualIF_close_retry(PNET_DEV dev)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 unsigned long generation=0;
 ULONG flags;
 int admitted,ret,consumed=0;
 if(!dev)return -1;
 adapter=RTMP_OS_NETDEV_GET_PRIV(dev);
 if(!adapter)return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 admitted=wr_iot_aux_close_retry_unmutated_down(&adapter->wr_iot_transition,
  adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,WR_REF_FAMILY_WDS,
  VIRTUAL_IF_NUM(adapter),&ticket,&generation);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!admitted)return -1;
 ret=wr_iot_virtual_down_checked(adapter,&ticket);
 if(ret!=NDIS_STATUS_SUCCESS){
  RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
  wr_iot_aux_close_retry_release(&adapter->wr_iot_transition,
   adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation,&ticket);
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
  return -1;
 }
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 consumed=wr_iot_aux_close_finalize_after_down(&adapter->wr_iot_transition,
  adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation,&ticket,3,
  VIRTUAL_IF_NUM(adapter));
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!consumed)return -1; /* retained owner must reconcile partial completion */
 wake_up_all(&adapter->wr_iot_ticket_wait);
 RT_MOD_DEC_USE_COUNT();
 return 0;
}

/* Recovery owner calls this only after DOWN was already verified and it
 * holds adapter/netdev lifetime. It must never repeat vendor DOWN. */
INT WdsVirtualIF_close_complete(PNET_DEV dev)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 unsigned long generation=0;
 ULONG flags;
 int admitted,consumed;
 if(!dev)return -1;
 adapter=RTMP_OS_NETDEV_GET_PRIV(dev);
 if(!adapter)return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 admitted=wr_iot_aux_close_claim_after_down(&adapter->wr_iot_transition,
  adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,WR_REF_FAMILY_WDS,
  VIRTUAL_IF_NUM(adapter),&ticket,&generation);
 consumed=admitted&&wr_iot_aux_close_finalize_after_down(
  &adapter->wr_iot_transition,adapter->wr_iot_interface_refs,
  WDEV_NUM_MAX+1,dev,generation,&ticket,5,VIRTUAL_IF_NUM(adapter));
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!consumed)return -1;
 wake_up_all(&adapter->wr_iot_ticket_wait);
 RT_MOD_DEC_USE_COUNT();
 return 0;
}

INT RT28xx_WDS_Remove(VOID *pAd)
{
	return RTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_WDS_REMOVE, 0, NULL, 0);
}

#endif /* WDS_SUPPORT */
