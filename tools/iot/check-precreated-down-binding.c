#include <assert.h>
#include <string.h>
#include "precreated-down-reference.h"

#include <errno.h>
typedef int INT;typedef unsigned long ULONG;typedef const void *PNET_DEV;
#define WDEV_NUM_MAX 2
enum {WR_PEER_OPEN_IDLE=0};
struct fake_adapter {
 int wr_iot_peer_delete_active;unsigned long wr_iot_peer_close_serial;
 struct {int phase,active_lease;} wr_iot_peer_open_owner;
 int chip,count;PNET_DEV net_dev;struct {int BssidNum;struct {struct {PNET_DEV if_dev;} wdev;} MBSSID[3];} ApCfg;
 int MacTabLock,wr_iot_transition_lock;
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;
 struct wr_iot_main_recovery_owner wr_iot_main_recovery;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[3];
 int wr_iot_control_users,wr_iot_control_poisoned,wr_iot_boot_active,wr_iot_boot_failed;
 struct {int active,poisoned;} wr_iot_driver_owner;
 struct {int active;} wr_iot_close_owner;
};
typedef struct fake_adapter *PRTMP_ADAPTER;
static int held,rtnl=1,running,locks,drift_peer;
static struct fake_adapter *drift_adapter;
#define IS_MT7603(ad) ((ad)->chip)
#define VIRTUAL_IF_NUM(ad) ((ad)->count)
#define RTMP_IRQ_LOCK(lock,flags) do{(void)(lock);(void)(flags);assert(!held);held=1;locks++;if(drift_peer&&locks==2)drift_adapter->wr_iot_peer_table_owner.transactions=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(lock);(void)(flags);assert(held);held=0;}while(0)
static int rtnl_is_locked(void){return rtnl;}
static int netif_running(PNET_DEV dev){assert(dev);return running;}
#include "precreated-down-binding.inc"
int main(void){
 int main_device=0,iot_device=0,peer_device=0;unsigned long sequence=0;
 struct wr_iot_interface_ref slots[3]={0};
 struct wr_iot_interface_ref *m=wr_iot_registry_add_family(slots,3,&sequence,&main_device,WR_REF_FAMILY_MAIN);
 struct wr_iot_interface_ref *i=wr_iot_registry_add_family(slots,3,&sequence,&iot_device,WR_REF_FAMILY_MBSS);
 struct wr_iot_interface_ref *p=wr_iot_registry_add_family(slots,3,&sequence,&peer_device,WR_REF_FAMILY_WDS);
 assert(m&&i&&p);m->published=i->published=p->published=1;
 struct wr_iot_radio_transition radio;wr_iot_radio_transition_init(&radio);
 radio.epoch=4;radio.serial=radio.retired_serial=7;
 struct wr_iot_main_recovery_owner owner;wr_iot_main_recovery_init(&owner);
 owner.last_release=(struct wr_iot_main_recovery_release_receipt){.device=&main_device,.generation=m->generation,.open_token=3,.close_serial=5,.ticket={.serial=7,.epoch=4,.operation=WR_RADIO_CLOSE,.prior_phase=WR_RADIO_READY,.prior_ready=1},.completion_epoch=4,.valid=1};
 m->last_token=3;m->close_serial=5;m->close_stage=4;m->close_epoch=4;
 m->close_vendor_count=1;m->close_prior_phase=WR_RADIO_READY;m->close_prior_ready=1;
 struct wr_iot_radio_transition saved_radio=radio;
 struct wr_iot_main_recovery_owner saved_owner=owner;
 struct wr_iot_interface_ref saved_slots[3];memcpy(saved_slots,slots,sizeof(slots));
#define CURRENT() wr_iot_precreated_down_reference(&owner,&radio,slots,3,&main_device,&iot_device,i->generation,0)
 assert(CURRENT());assert(!memcmp(&radio,&saved_radio,sizeof(radio))&&!memcmp(&owner,&saved_owner,sizeof(owner))&&!memcmp(slots,saved_slots,sizeof(slots)));
 i->last_token=1;assert(!CURRENT());*i=saved_slots[1];
 i->close_serial=1;assert(!CURRENT());*i=saved_slots[1];
 i->open_unmutated=1;assert(!CURRENT());*i=saved_slots[1];
 i->removing=1;assert(!CURRENT());*i=saved_slots[1];
 p->phase=WR_REF_RESERVED;assert(!CURRENT());*p=saved_slots[2];
 p->close_running=1;assert(!CURRENT());*p=saved_slots[2];
 radio.active_tx=1;assert(!CURRENT());radio=saved_radio;
 radio.epoch++;assert(!CURRENT());radio=saved_radio;
 radio.phase=WR_RADIO_READY;assert(!CURRENT());radio=saved_radio;
 owner.last_release.valid=0;assert(!CURRENT());owner=saved_owner;
 owner.deferred_owners=1;assert(!CURRENT());owner=saved_owner;
 owner.device=&main_device;assert(!CURRENT());owner=saved_owner;
 owner.close_ticket_valid=1;assert(!CURRENT());owner=saved_owner;
 owner.schedule_recorded=1;assert(!CURRENT());owner=saved_owner;
 owner.open_token=3;assert(!CURRENT());owner=saved_owner;
 assert(!wr_iot_precreated_down_reference(&owner,&radio,slots,3,&main_device,&iot_device,i->generation,1));
 assert(CURRENT());
 struct wr_iot_peer_table_owner table={0};struct wr_iot_peer_close_executor executor={0};
 assert(!wr_iot_precreated_down_peers_current(&table,&executor));table.closed=1;
 assert(wr_iot_precreated_down_peers_current(&table,&executor));
 table.transactions=1;assert(!wr_iot_precreated_down_peers_current(&table,&executor));table.transactions=0;
 table.retained=1;assert(!wr_iot_precreated_down_peers_current(&table,&executor));table.retained=0;
 table.poisoned=1;assert(!wr_iot_precreated_down_peers_current(&table,&executor));table.poisoned=0;
 table.active=1;assert(!wr_iot_precreated_down_peers_current(&table,&executor));table.active=0;
 executor.running=1;assert(!wr_iot_precreated_down_peers_current(&table,&executor));executor.running=0;
 executor.retained=1;assert(!wr_iot_precreated_down_peers_current(&table,&executor));executor.retained=0;
 executor.serial=1;assert(!wr_iot_precreated_down_peers_current(&table,&executor));executor.serial=0;
 assert(wr_iot_precreated_down_peers_current(&table,&executor));
 struct fake_adapter ad={0};ad.chip=1;ad.net_dev=&main_device;ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.if_dev=&iot_device;
 ad.wr_iot_main_recovery=owner;ad.wr_iot_transition=radio;memcpy(ad.wr_iot_interface_refs,slots,sizeof(slots));ad.wr_iot_peer_table_owner=table;
 struct fake_adapter before=ad;
 assert(!wr_iot_precreated_down_observed(&ad,&iot_device,i->generation)&&!held&&!memcmp(&ad,&before,sizeof(ad)));
 rtnl=0;assert(wr_iot_precreated_down_observed(&ad,&iot_device,i->generation)==-EBUSY);rtnl=1;
 running=1;assert(wr_iot_precreated_down_observed(&ad,&iot_device,i->generation)==-EAGAIN);running=0;
 ad.wr_iot_control_users=1;assert(wr_iot_precreated_down_observed(&ad,&iot_device,i->generation)==-EAGAIN);ad=before;
 ad.wr_iot_peer_table_owner.transactions=1;assert(wr_iot_precreated_down_observed(&ad,&iot_device,i->generation)==-EAGAIN);ad=before;
 ad.wr_iot_peer_delete_active=1;assert(wr_iot_precreated_down_observed(&ad,&iot_device,i->generation)==-EAGAIN);ad=before;
 ad.wr_iot_peer_close_serial=1;assert(wr_iot_precreated_down_observed(&ad,&iot_device,i->generation)==-EAGAIN);ad=before;
 ad.wr_iot_peer_open_owner.phase=1;assert(wr_iot_precreated_down_observed(&ad,&iot_device,i->generation)==-EAGAIN);ad=before;
 ad.wr_iot_peer_open_owner.active_lease=1;assert(wr_iot_precreated_down_observed(&ad,&iot_device,i->generation)==-EAGAIN);ad=before;
 locks=0;drift_peer=1;drift_adapter=&ad;
 assert(wr_iot_precreated_down_observed(&ad,&iot_device,i->generation)==-EAGAIN&&!held);
 drift_peer=0;ad=before;
 assert(!wr_iot_precreated_down_observed(&ad,&iot_device,i->generation)&&!held);
 return 0;
}
