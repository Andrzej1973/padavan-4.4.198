/*
 ***************************************************************************
 * Ralink Tech Inc.
 * 4F, No. 2 Technology 5th Rd.
 * Science-based Industrial Park
 * Hsin-chu, Taiwan, R.O.C.
 *
 * (c) Copyright 2002-2006, Ralink Technology, Inc.
 *
 * All rights reserved. Ralink's source code is an unpublished work and the
 * use of a copyright notice does not imply otherwise. This source code
 * contains confidential trade secret material of Ralink Tech. Any attemp
 * or participation in deciphering, decoding, reverse engineering or in any
 * way altering the source code is stricitly prohibited, unless the prior
 * written consent of Ralink Technology, Inc. is obtained.
 ***************************************************************************

    Module Name:
    ap_apcli.c

    Abstract:
    Support AP-Client function.

    Note:
    1. Call RT28xx_ApCli_Init() in init function and
       call RT28xx_ApCli_Remove() in close function

    2. MAC of ApCli-interface is initialized in RT28xx_ApCli_Init()

    3. ApCli index (0) of different rx packet is got in

    4. ApCli index (0) of different tx packet is assigned in

    5. ApCli index (0) of different interface is got in APHardTransmit() by using

    6. ApCli index (0) of IOCTL command is put in pAd->OS_Cookie->ioctl_if

    8. The number of ApCli only can be 1

	9. apcli convert engine subroutines, we should just take care data packet.
    Revision History:
    Who             When            What
    --------------  ----------      ----------------------------------------------
    Shiang, Fonchi  02-13-2007      created
*/
#define RTMP_MODULE_OS

#ifdef APCLI_SUPPORT

/*#include "rt_config.h" */
#include "rtmp_comm.h"
#include "rt_os_util.h"
#include "rt_os_net.h"
#include "rt_config.h"
#include "virtual-open-claim.h"


/*
========================================================================
Routine Description:
    Init AP-Client function.

Arguments:
    pAd            points to our adapter
    main_dev_p      points to the main BSS network interface

Return Value:
    None

Note:
	1. Only create and initialize virtual network interfaces.
	2. No main network interface here.
========================================================================
*/
VOID RT28xx_ApCli_Init(VOID *pAd, PNET_DEV main_dev_p)
{
	RTMP_OS_NETDEV_OP_HOOK netDevOpHook;

	/* init operation functions */
	NdisZeroMemory(&netDevOpHook, sizeof(RTMP_OS_NETDEV_OP_HOOK));
	netDevOpHook.open = ApCli_VirtualIF_Open;
	netDevOpHook.stop = ApCli_VirtualIF_Close;
	netDevOpHook.xmit = rt28xx_send_packets;
	netDevOpHook.ioctl = rt28xx_ioctl;
	RTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_APC_INIT,
						0, &netDevOpHook, 0);
}

/*
========================================================================
Routine Description:
    Open a virtual network interface.

Arguments:
    dev_p           which WLAN network interface

Return Value:
    0: open successfully
    otherwise: open fail

Note:
========================================================================
*/
INT ApCli_VirtualIF_Open(PNET_DEV dev_p)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record;
 unsigned long generation=0;
 ULONG flags;
 int admitted,up=0,apcli_attempted=0,apcli_ok=0,finished,ready,owned,retain_pin=1;
 if(!dev_p)return -1;
 RT_MOD_INC_USE_COUNT();
 adapter=RTMP_OS_NETDEV_GET_PRIV(dev_p);
 if(!adapter){RT_MOD_DEC_USE_COUNT();return -1;}
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 /* Physical first-open recovery is unresolved; require an existing owner. */
 admitted=VIRTUAL_IF_NUM(adapter)>0 &&
  wr_iot_aux_open_reserve(&adapter->wr_iot_transition,
   adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev_p,WR_REF_FAMILY_APCLI,
   VIRTUAL_IF_NUM(adapter),&ticket,&generation);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if(!admitted){RT_MOD_DEC_USE_COUNT();return -1;}
 up=VIRTUAL_IF_UP_CLAIM(adapter,dev_p,&ticket,generation)==0;
 if(up){
  apcli_attempted=1;
  apcli_ok=RTMP_AP_IoctlHandle(adapter,NULL,CMD_RTPRIV_IOCTL_APC_OPEN,
                              0,dev_p,0)==NDIS_STATUS_SUCCESS;
 }
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find(adapter->wr_iot_interface_refs,
                            WDEV_NUM_MAX+1,dev_p,generation);
 finished=wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,
                              up&&apcli_ok);
 ready=wr_iot_aux_open_accepted(&adapter->wr_iot_transition,&ticket,finished);
 owned=ready&&up&&apcli_ok&&record&&
  wr_iot_ref_complete_aux_open(record,dev_p,generation,ticket.serial,
                               1,1,1,1,1,&retain_pin);
 if(!owned&&record&&record->phase==WR_REF_RESERVED)
  wr_iot_ref_complete_aux_open(record,dev_p,generation,ticket.serial,
                               1,1,up&&ready,apcli_attempted,
                               apcli_ok&&ready,&retain_pin);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 wake_up_all(&adapter->wr_iot_ticket_wait);
 /* APC_OPEN may fail after mutating the adapter. Failed ndo_open has no
  * guaranteed stop callback, so keep the pin for checked recovery. */
 if(!owned)return -1;
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 RT_MOD_HNAT_REG(dev_p);
#endif
#ifdef MTFWD
 RTMP_OS_NETDEV_CARRIER_OFF(dev_p);
#endif
 return 0;
}

INT ApCli_VirtualIF_Close(PNET_DEV dev_p)
{
	VOID *pAd;

	pAd = RTMP_OS_NETDEV_GET_PRIV(dev_p);
	ASSERT(pAd);

	DBGPRINT(RT_DEBUG_TRACE, ("%s: ===> %s\n", __FUNCTION__, RTMP_OS_NETDEV_GET_DEVNAME(dev_p)));


	RTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_APC_CLOSE, 0, dev_p, 0);

#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
	RT_MOD_HNAT_DEREG(dev_p);
#endif

	VIRTUAL_IF_DOWN(pAd, dev_p);

	RT_MOD_DEC_USE_COUNT();

	return 0;
}


/*
========================================================================
Routine Description:
    Remove ApCli-BSS network interface.

Arguments:
    pAd            points to our adapter

Return Value:
    None

Note:
========================================================================
*/
INT RT28xx_ApCli_Remove(VOID *pAd)
{

	return RTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_APC_REMOVE, 0, NULL, 0);


}

#endif /* APCLI_SUPPORT */

