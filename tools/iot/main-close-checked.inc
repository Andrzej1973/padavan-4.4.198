/* Partial main ndo_stop binding for an isolated candidate only. Linux ignores
 * its return value; all failure paths retain the open module pin and require
 * a separately bound, adapter-pinned recovery owner before production use. */
/* Resume only a preclose receipt that already completed RTMPInfClose. The
 * deferred owner must pin adapter/netdev lifetime and supply the exact ticket.
 * The caller performs the module decrement only after this returns success. */
static int wr_iot_main_close_continue_checked(PRTMP_ADAPTER adapter,
 struct net_device *net_dev,unsigned long generation,unsigned long token,
 const struct wr_iot_radio_ticket *ticket)
{
 struct wr_iot_interface_ref *record;
 ULONG flags;
 unsigned int close_stage;
 int physical_receipt, release_pin = 0;

 if (!adapter || !net_dev || !ticket) return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
                               WDEV_NUM_MAX + 1, net_dev, generation);
 if (!record || !wr_iot_main_close_receipt_matches(record, ticket) ||
     record->last_token != token ||
     (record->close_stage != 2U && record->close_stage != 3U)) {
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  return -1;
 }
 close_stage = record->close_stage;
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);

 if (close_stage == 2U &&
     wr_iot_virtual_down_checked(adapter, ticket) != NDIS_STATUS_SUCCESS)
  return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
                               WDEV_NUM_MAX + 1, net_dev, generation);
 /* Checked software shutdown receipt; callback/DMA quiescence remains a
  * separate PCI release gate. */
 physical_receipt = ticket->operation != WR_RADIO_CLOSE ||
  (adapter->wr_iot_transition.shutdown_stage == 2U &&
   adapter->wr_iot_transition.mt_radio_off_stage == 4U &&
   adapter->wr_iot_transition.virtual_down_stage == 2U);
 if (!record ||
     (close_stage == 2U &&
      !wr_iot_main_close_note_checked_down(record, ticket, 1,
                                           physical_receipt)) ||
     !wr_iot_main_stop_complete(&adapter->wr_iot_transition, record,
       net_dev, generation, token, ticket, 1, physical_receipt,
       &release_pin)) {
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  return -1;
 }
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 wake_up_all(&adapter->wr_iot_ticket_wait);
 return release_pin ? 0 : -1;
}

/* Shared ticket admission for ndo_stop and a deferred acquired-open owner.
 * Both callers must already pin the netdev and adapter for this operation. */
static int wr_iot_main_close_begin_checked(PRTMP_ADAPTER adapter,
 struct net_device *net_dev,struct wr_iot_radio_ticket *ticket,
 unsigned long *generation,unsigned long *token,unsigned long *wait_serial)
{
 struct wr_iot_interface_ref *record;
 enum wr_iot_main_stop_result admission;
 ULONG flags;
 unsigned int vendor_count;

 if (!adapter || !net_dev || !ticket || !generation || !token ||
     !wait_serial) return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 vendor_count = VIRTUAL_IF_NUM(adapter);
 admission = wr_iot_main_stop_request(&adapter->wr_iot_transition,
  adapter->wr_iot_interface_refs, WDEV_NUM_MAX + 1,
  adapter->net_dev, net_dev, vendor_count, ticket, wait_serial);
 if (admission != WR_MAIN_STOP_ADMITTED) {
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  /* WAIT_TICKET and NEEDS_RECOVERY must hand off to the deferred owner.
   * Until that owner is bound, this source may not enter a firmware image. */
  return -1;
 }
 record = wr_iot_registry_find_owned(adapter->wr_iot_interface_refs,
                                    WDEV_NUM_MAX + 1, net_dev);
 if (!record) {
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  return -1; /* Keep ticket and pin for recovery. */
 }
 *generation = record->generation;
 *token = record->last_token;
 if (!wr_iot_ref_begin_close(record, net_dev, *generation, *token) ||
     !wr_iot_main_close_claim_preclose(&adapter->wr_iot_transition,
       record, adapter->wr_iot_interface_refs, WDEV_NUM_MAX + 1,
       ticket, vendor_count)) {
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  return -1; /* An admitted close is never silently retired. */
 }
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 return 0;
}

/* This stage is one-shot: never call it on a retained stage-2/3 ticket. */
static int wr_iot_main_close_preclose_once(PRTMP_ADAPTER adapter,
 struct net_device *net_dev,unsigned long generation,
 const struct wr_iot_radio_ticket *ticket)
{
 struct wr_iot_interface_ref *record;
 ULONG flags;
 if (!adapter || !net_dev || !ticket) return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
                               WDEV_NUM_MAX + 1, net_dev, generation);
 if (!record || !wr_iot_main_close_claim_void_preclose(record, ticket)) {
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  return -1;
 }
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 RT_MOD_HNAT_DEREG(net_dev);
#endif
 netif_carrier_off(net_dev);
 netif_stop_queue(net_dev);
 /* Void vendor preclose mutates software state; its attempt was recorded. */
 RTMPInfClose(adapter);
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
                               WDEV_NUM_MAX + 1, net_dev, generation);
 if (!record || !wr_iot_main_close_finish_preclose(record, ticket)) {
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  return -1;
 }
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 return 0;
}

int MainVirtualIF_close(IN struct net_device *net_dev)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_radio_ticket ticket;
 unsigned long generation, token, wait_serial = 0;

 if (!net_dev) return -1;
 adapter = RTMP_OS_NETDEV_GET_PRIV(net_dev);
 if (!adapter) return -1;
 if (wr_iot_main_close_begin_checked(adapter, net_dev, &ticket,
                                     &generation, &token, &wait_serial) != 0)
  return -1;
 if (wr_iot_main_close_preclose_once(adapter, net_dev, generation,
                                    &ticket) != 0)
  return -1;

 if (wr_iot_main_close_continue_checked(adapter, net_dev, generation,
                                        token, &ticket) != 0)
  return -1;
 RT_MOD_DEC_USE_COUNT();
 return 0;
}

/* Execute one already accepted deferred owner. The Linux work callback must
 * supply adapter/netdev lifetime pins, call this outside RTNL and the shared
 * lock, and arrange external join/reap before reusing the work_struct. */
static int wr_iot_main_recovery_execute(PRTMP_ADAPTER adapter)
{
 struct wr_iot_main_recovery_owner *owner;
 struct wr_iot_interface_ref *record;
 struct net_device *net_dev;
 struct wr_iot_radio_ticket ticket;
 enum wr_iot_main_recovery_action action;
 unsigned long generation, token, wait_serial = 0;
 ULONG flags;
 unsigned int vendor_count;
 int bound, marked, released;

 if (!adapter) return -1;
 owner = &adapter->wr_iot_main_recovery;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 if (!wr_iot_main_recovery_begin(owner)) {
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  return -1;
 }
 net_dev = (struct net_device *)owner->device;
 generation = owner->generation;
 token = owner->open_token;
 vendor_count = VIRTUAL_IF_NUM(adapter);
 record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
                               WDEV_NUM_MAX + 1, net_dev, generation);
 action = wr_iot_main_recovery_action(owner, record,
  &adapter->wr_iot_transition, adapter->wr_iot_interface_refs,
  WDEV_NUM_MAX + 1, vendor_count);
 if (action == WR_MAIN_RECOVERY_CONTINUE_CLOSE)
  ticket = owner->close_ticket;
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);

 if (action == WR_MAIN_RECOVERY_BEGIN_CLOSE) {
  if (wr_iot_main_close_begin_checked(adapter, net_dev, &ticket,
                                      &generation, &token, &wait_serial) != 0)
   goto retain;
  RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
  record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
                                WDEV_NUM_MAX + 1, net_dev, generation);
  bound = wr_iot_main_recovery_bind_close(owner, record,
            &adapter->wr_iot_transition, &ticket);
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  if (!bound) goto retain;
  if (wr_iot_main_close_preclose_once(adapter, net_dev, generation,
                                      &ticket) != 0) {
   RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
   record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
                                 WDEV_NUM_MAX + 1, net_dev, generation);
   wr_iot_main_recovery_preclose_uncertain(owner, record);
   RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
   goto retain;
  }
 } else if (action != WR_MAIN_RECOVERY_CONTINUE_CLOSE) {
  goto retain;
 }

 if (wr_iot_main_close_continue_checked(adapter, net_dev, generation,
                                        token, &ticket) != 0)
  goto retain;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
                               WDEV_NUM_MAX + 1, net_dev, generation);
 marked = wr_iot_main_recovery_mark_completed(owner, record);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 if (!marked) goto retain;
 RT_MOD_DEC_USE_COUNT();
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 released = wr_iot_main_recovery_mark_module_pin_released(owner, 1, 1);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 return released ? 0 : -1;

retain:
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 wr_iot_main_recovery_retain(owner);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 return -1;
}
