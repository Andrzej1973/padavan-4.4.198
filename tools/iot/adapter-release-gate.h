/* Host-only PCI adapter release gate; no vendor binding. Caller holds the
 * shared adapter lock for radio/registry/owner counters and has separately
 * proven callback and physical quiescence outside that lock. PCI observation
 * is an additional necessary condition, never sufficient DMA proof. */
#ifndef WR_IOT_ADAPTER_RELEASE_GATE_H
#define WR_IOT_ADAPTER_RELEASE_GATE_H
#include "all-child-teardown.h"
#include "interface-registry.h"
#include "radio-transition.h"
#include "pci-transaction-observer.h"

static inline int wr_iot_adapter_release_gate(
 const struct wr_child_teardown *children,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *refs,unsigned int count,
 unsigned int registration_inflight,unsigned int deferred_owners,
 int callbacks_quiescent,int physical_quiescent,
 const struct wr_iot_pci_observation *pci_observation){
 unsigned int i;
 if(!children||!radio||!refs||children->phase!=WR_CHILD_DONE||
    !radio->retiring||radio->phase!=WR_RADIO_DOWN||radio->busy||
    radio->active_tx||radio->reset_pending||radio->main_ready||
    registration_inflight||deferred_owners||
    !callbacks_quiescent||!physical_quiescent||
    !pci_observation||!radio->epoch||
    pci_observation->radio_epoch!=radio->epoch||
    pci_observation->result!=WR_IOT_PCI_TX_CLEAR_OBSERVED)return 0;
 for(i=0;i<count;i++)
  if(refs[i].device||refs[i].published||refs[i].removing||
     refs[i].phase!=WR_REF_IDLE)return 0;
 return 1;
}
#endif
