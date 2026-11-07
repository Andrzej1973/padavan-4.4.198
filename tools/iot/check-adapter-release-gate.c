#include "adapter-release-gate.h"
#include <assert.h>
#include <stdio.h>

int main(void){
 struct wr_child_teardown children;
 struct wr_iot_radio_transition radio;
 struct wr_iot_interface_ref refs[2];
 struct wr_iot_pci_observation pci_observation = {
  WR_IOT_PCI_TX_CLEAR_OBSERVED, 1UL};
 struct wr_iot_pci_observation invalid_observation = {
  WR_IOT_PCI_TX_INVALID, 1UL};
 struct wr_iot_pci_observation master_observation = {
  WR_IOT_PCI_TX_MASTER_ACTIVE, 1UL};
 struct wr_iot_pci_observation pending_observation = {
  WR_IOT_PCI_TX_PENDING, 1UL};
 int dev=0;
 wr_child_teardown_init(&children);
 wr_iot_radio_transition_init(&radio);
 wr_iot_ref_init(&refs[0],0,0);
 wr_iot_ref_init(&refs[1],0,0);
 assert(wr_child_teardown_begin(&children,0,1));
 radio.retiring=1;radio.phase=WR_RADIO_DOWN;
 assert(wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1,&pci_observation));
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1,0));
 radio.epoch++;
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1,&pci_observation));
 pci_observation.radio_epoch=radio.epoch;
 invalid_observation.radio_epoch=radio.epoch;
 master_observation.radio_epoch=radio.epoch;
 pending_observation.radio_epoch=radio.epoch;
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1,&invalid_observation));
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1,&master_observation));
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1,&pending_observation));
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,1,1,1,&pci_observation));
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,1,0,1,1,&pci_observation));
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,0,1,&pci_observation));
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,0,&pci_observation));
 wr_iot_ref_init(&refs[0],&dev,1);refs[0].published=1;
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1,&pci_observation));
 assert(wr_iot_registry_begin_remove(&refs[0],&dev,1));
 assert(wr_iot_registry_kernel_done(&refs[0],&dev,1));
 assert(wr_iot_registry_vendor_done(&refs[0],&dev,1));
 assert(wr_iot_registry_release(&refs[0],&dev,1));
 radio.reset_pending=WR_RADIO_RESET_PDMA;
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1,&pci_observation));
 radio.reset_pending=0;radio.busy=WR_RADIO_CLOSE;
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1,&pci_observation));
 radio.busy=0;radio.phase=WR_RADIO_CLOSING;
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1,&pci_observation));
 radio.phase=WR_RADIO_DOWN;
 assert(wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1,&pci_observation));
 wr_child_teardown_init(&children);
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,0,1,1,&pci_observation));
 puts("PASS adapter release gate: no deferred owner or live radio/reference");
 return 0;
}
