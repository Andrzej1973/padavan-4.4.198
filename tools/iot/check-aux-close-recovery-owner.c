#include "aux-close-recovery-owner.h"
#include "adapter-release-gate.h"
#include <assert.h>
#include <stdio.h>

int main(void){
 struct wr_iot_aux_close_recovery owner;
 struct wr_iot_radio_transition radio;
 struct wr_iot_interface_ref refs[2]={{0}};
 struct wr_iot_interface_ref empty[2]={{0}};
 struct wr_child_teardown children;
 struct wr_iot_pci_observation pci_observation = {
  WR_IOT_PCI_TX_CLEAR_OBSERVED, 1UL};
 int main_dev=0,aux_dev=0;
 wr_iot_aux_close_recovery_init(&owner);
 wr_iot_radio_transition_init(&radio);
 wr_child_teardown_init(&children);
 wr_iot_ref_init(&refs[0],&main_dev,1);
 wr_iot_ref_init(&refs[1],&aux_dev,2);
 refs[1].family=WR_REF_FAMILY_WDS;
 refs[1].phase=WR_REF_CLOSING;refs[1].close_stage=1;
 refs[1].close_serial=7;radio.busy=WR_RADIO_AUX_CLOSE;radio.serial=7;
 refs[1].family=WR_REF_FAMILY_APCLI;
 assert(!wr_iot_aux_close_recovery_queue(&owner,&refs[1],&radio,1,1));
 refs[1].family=WR_REF_FAMILY_MONITOR;
 assert(!wr_iot_aux_close_recovery_queue(&owner,&refs[1],&radio,1,1));
 refs[1].family=WR_REF_FAMILY_WDS;
 assert(!wr_iot_aux_close_recovery_queue(&owner,&refs[1],&radio,1,0));
 assert(!wr_iot_aux_close_recovery_queue(&owner,&refs[1],&radio,0,1));
 assert(wr_iot_aux_close_recovery_queue(&owner,&refs[1],&radio,1,1));
 assert(owner.deferred_owners==1&&owner.phase==WR_RECOVERY_QUEUED);
 assert(!wr_iot_aux_close_recovery_queue(&owner,&refs[1],&radio,1,1));
 assert(wr_iot_aux_close_recovery_begin(&owner));
 assert(wr_iot_aux_close_recovery_action(&owner,&refs[1],&radio)==
        WR_RECOVERY_RETRY_DOWN);
 refs[1].close_stage=4;
 assert(wr_iot_aux_close_recovery_action(&owner,&refs[1],&radio)==
        WR_RECOVERY_COMPLETE_AFTER_DOWN);
 refs[1].family=WR_REF_FAMILY_APCLI;
 assert(wr_iot_aux_close_recovery_action(&owner,&refs[1],&radio)==
        WR_RECOVERY_NO_ACTION);
 refs[1].family=WR_REF_FAMILY_WDS;
 refs[1].close_serial=8;
 assert(wr_iot_aux_close_recovery_action(&owner,&refs[1],&radio)==
        WR_RECOVERY_NO_ACTION);
 refs[1].close_serial=7;refs[1].close_stage=1;
 assert(wr_iot_aux_close_recovery_retain(&owner));
 assert(wr_iot_aux_close_recovery_action(&owner,&refs[1],&radio)==
        WR_RECOVERY_NO_ACTION);
 assert(wr_iot_aux_close_recovery_requeue(&owner,2));
 assert(wr_iot_aux_close_recovery_begin(&owner));
 assert(wr_iot_aux_close_recovery_action(&owner,&refs[1],&radio)==
        WR_RECOVERY_RETRY_DOWN);
 assert(wr_iot_aux_close_recovery_retain(&owner));
 assert(!wr_iot_aux_close_recovery_requeue(&owner,2));
 children.phase=WR_CHILD_DONE;radio.retiring=1;radio.phase=WR_RADIO_DOWN;
 radio.busy=0;
 assert(!wr_iot_adapter_release_gate(&children,&radio,empty,2,0,
                                     owner.deferred_owners,1,1,&pci_observation));
 assert(!wr_iot_adapter_release_gate(&children,&radio,refs,2,0,
                                     owner.deferred_owners,1,1,&pci_observation));
 assert(wr_iot_aux_close_recovery_request_stop(&owner));
 assert(owner.phase==WR_RECOVERY_STOPPING);
 assert(!wr_iot_aux_close_recovery_mark_completed(&owner,&refs[1],&radio));
 assert(!wr_iot_aux_close_recovery_complete(&owner,1));
 refs[1].phase=WR_REF_IDLE;refs[1].close_stage=2;
 radio.busy=0;
 assert(!wr_iot_aux_close_recovery_mark_completed(&owner,&refs[1],&radio));
 radio.retired_serial=7;
 assert(wr_iot_aux_close_recovery_mark_completed(&owner,&refs[1],&radio));
 assert(!wr_iot_aux_close_recovery_mark_completed(&owner,&refs[1],&radio));
 assert(!wr_iot_adapter_release_gate(&children,&radio,empty,2,0,
                                     owner.deferred_owners,1,1,&pci_observation));
 radio.retired_serial=8; /* unrelated operation after checked close */
 assert(!wr_iot_aux_close_recovery_complete(&owner,0));
 assert(wr_iot_aux_close_recovery_complete(&owner,1));
 assert(owner.deferred_owners==0&&owner.phase==WR_RECOVERY_IDLE);
 assert(wr_iot_adapter_release_gate(&children,&radio,empty,2,0,
                                    owner.deferred_owners,1,1,&pci_observation));
 puts("PASS deferred auxiliary close retains adapter until joined completion");
 return 0;
}
