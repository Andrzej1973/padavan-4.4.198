#include "pci-retirement-owner.h"
#include <assert.h>
#include <stdio.h>

int main(void){
 struct wr_iot_pci_retirement owner;
 struct wr_child_teardown children;
 struct wr_iot_radio_transition radio;
 struct wr_iot_interface_ref refs[1];
 wr_iot_pci_retirement_init(&owner);
 wr_child_teardown_init(&children);
 wr_iot_radio_transition_init(&radio);
 wr_iot_ref_init(&refs[0],0,0);
 assert(!wr_iot_pci_retirement_begin(&owner,&radio,1));
 radio.retiring=1;
 assert(!wr_iot_pci_retirement_begin(&owner,&radio,0));
 assert(wr_iot_pci_retirement_begin(&owner,&radio,1));
 assert(!wr_iot_pci_retirement_work_joined(&owner,0));
 assert(!wr_iot_pci_retirement_children_done(&owner,&children,0));
 assert(!wr_iot_pci_retirement_work_joined(&owner,1));
 assert(!wr_iot_pci_retirement_stop_requested(&owner,0));
 assert(wr_iot_pci_retirement_stop_requested(&owner,1));
 assert(!wr_iot_pci_retirement_stop_requested(&owner,1));
 assert(wr_iot_pci_retirement_work_joined(&owner,1));
 assert(wr_child_teardown_begin(&children,WR_CHILD_WDS,1));
 assert(!wr_iot_pci_retirement_children_done(&owner,&children,0));
 assert(!wr_child_teardown_complete(&children,WR_CHILD_WDS));
 assert(wr_child_teardown_close_done(&children,WR_CHILD_WDS,1));
 assert(wr_child_teardown_complete(&children,WR_CHILD_WDS));
 assert(!wr_iot_pci_retirement_children_done(&owner,&children,1));
 assert(wr_iot_pci_retirement_children_done(&owner,&children,0));
 assert(!wr_iot_pci_retirement_main_detached(&owner,0,1));
 assert(!wr_iot_pci_retirement_main_detached(&owner,1,0));
 assert(wr_iot_pci_retirement_main_detached(&owner,1,1));
 radio.phase=WR_RADIO_CLOSING;
 assert(!wr_iot_pci_retirement_claim_release(&owner,&children,&radio,
                                            refs,1,0,0,1,1));
 radio.phase=WR_RADIO_DOWN;
 assert(!wr_iot_pci_retirement_claim_release(&owner,&children,&radio,
                                            refs,1,0,0,0,1));
 assert(!wr_iot_pci_retirement_claim_release(&owner,&children,&radio,
                                            refs,1,0,0,1,0));
 assert(wr_iot_pci_retirement_claim_release(&owner,&children,&radio,
                                           refs,1,0,0,1,1));
 assert(!wr_iot_pci_retirement_claim_release(&owner,&children,&radio,
                                            refs,1,0,0,1,1));
 puts("PASS PCI retirement owner: release requires ordered quiescence");
 return 0;
}
