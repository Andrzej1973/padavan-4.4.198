"""Bind retained ARM identity at actual Main recovery continuation entry.

Pure reviewed source transform; separate installer/endpoint integration needed.
"""
def compose(source):
    marker='static int wr_iot_main_recovery_execute('
    if source.count(marker)!=1:
        raise ValueError('ambiguous Main recovery worker')
    start=source.index(marker);end=source.index('\n}',start)+2
    body=source[start:end]
    anchor=' if (wr_iot_main_close_continue_checked(adapter, net_dev, generation,'
    if body.count(anchor)!=1 or 'wr_iot_physical_stop_lifetime_capture_main' in body:
        raise ValueError('changed/already-bound Main continuation')
    guard=''' /* Same existing transition lock; no nested MacTabLock or work joins.
  * Retain the exact accepted worker ticket before physical close starts. */
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 bound = 1;
 if (adapter->wr_iot_physical_lifetime.active) {
  struct wr_iot_radio_ticket physical_ticket;
  record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
                                WDEV_NUM_MAX + 1, net_dev, generation);
  bound = wr_iot_physical_stop_lifetime_capture_main(
    &adapter->wr_iot_physical_lifetime,
    adapter->wr_iot_physical_lifetime.serial, owner,
    &adapter->wr_iot_transition, record, &physical_ticket);
 }
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 if (!bound) goto retain;
'''
    body=body.replace(anchor,guard+anchor,1)
    return source[:start]+body+source[end:]
