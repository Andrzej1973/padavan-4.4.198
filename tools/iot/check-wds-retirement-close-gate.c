#include "aux-close-claim.h"
#include <assert.h>
#include <string.h>

int main(void)
{
 struct wr_iot_interface_ref slots[2]={0}, before[2];
 struct wr_iot_interface_ref *main_ref,*wds;
 struct wr_iot_radio_transition radio, saved;
 struct wr_iot_radio_ticket ticket;
 unsigned long seq=0,generation=99;
 int main_dev=0,wds_dev=0;
 wr_iot_radio_transition_init(&radio);
 radio.phase=WR_RADIO_READY;radio.main_ready=1;
 main_ref=wr_iot_registry_add_family(slots,2,&seq,&main_dev,WR_REF_FAMILY_MAIN);
 wds=wr_iot_registry_add_family(slots,2,&seq,&wds_dev,WR_REF_FAMILY_WDS);
 assert(main_ref&&wds);
 main_ref->published=wds->published=1;
 main_ref->phase=wds->phase=WR_REF_OWNED;
 main_ref->last_token=wds->last_token=1;
 assert(wr_iot_wds_peer_operation_begin_remove(&wds->peer_operation,&wds_dev,wds->generation));
 memcpy(before,slots,sizeof slots);memcpy(&saved,&radio,sizeof radio);
 assert(!wr_iot_ref_begin_close(wds,&wds_dev,wds->generation,1));
 assert(!wr_iot_aux_close_reserve(&radio,slots,2,&wds_dev,WR_REF_FAMILY_WDS,2,&ticket,&generation));
 assert(generation==99&&!memcmp(before,slots,sizeof slots)&&!memcmp(&saved,&radio,sizeof radio));
 /* An idle registration must remain retained as well. */
 wds->phase=WR_REF_IDLE;
 memcpy(before,slots,sizeof slots);
 assert(!wr_iot_registry_begin_remove(wds,&wds_dev,wds->generation));
 assert(!wr_iot_registry_release(wds,&wds_dev,wds->generation));
 assert(!memcmp(before,slots,sizeof slots));
 /* Only fresh initialization is used here, not a production retirement release. */
 wr_iot_wds_peer_operation_init(&wds->peer_operation,&wds_dev,wds->generation);
 wds->phase=WR_REF_OWNED;
 assert(wr_iot_aux_close_reserve(&radio,slots,2,&wds_dev,WR_REF_FAMILY_WDS,2,&ticket,&generation));
 return 0;
}
