"""Synthetic adapter additions for extracted stage53+ close paths only."""
def enabled(candidate):
    return (candidate/'include/wr-iot-peer-close-executor.inc').exists()

def body(source,signature):
    start=source.index(signature)
    return source[start:source.index('\n}',start)+2]

def definitions(source):
    return (body(source,'static INT wr_iot_legacy_close_body(')+'\n'+
            body(source,'static INT wr_iot_checked_close_body(')+'\n'+
            '#include "wr-iot-peer-close-executor.inc"\n')

def prefix(text):
    text=text.replace('#define MAC_TABLE int','''
#include "peer-table-owner.h"
#include "peer-close-executor.h"
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_TR_TABLE 3
typedef unsigned int UINT;
typedef struct {int live;} MAC_TABLE_ENTRY;
typedef struct {int wr_iot_setup_observed,wr_iot_setup_result;} STA_TR_ENTRY;
typedef struct {unsigned int Size;MAC_TABLE_ENTRY Content[4];STA_TR_ENTRY tr_entry[3];} MAC_TABLE;
#define IS_ENTRY_NONE(e) (!(e)->live)
''')
    extra=('MAC_TABLE MacTab;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;'
           'unsigned long wr_iot_peer_close_serial;unsigned int wr_iot_peer_legacy_close_state;unsigned int wr_iot_peer_delete_active;'
           'struct wr_iot_peer_close_executor wr_iot_peer_close_executor;')
    if 'MacTabLock' not in text:
        extra+='int MacTabLock;'
    text=text.replace('int MacTab;',extra)
    text+='''
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
#include "wr-iot-peer-close-table.inc"
#include "wr-iot-peer-legacy-close.inc"
#ifndef RtmpMgmtTaskExit
#define RtmpMgmtTaskExit(ad) ((void)(ad),joins++)
#endif
/* Each call represents a fresh fixture adapter, never a production reset. */
static void wr_test_peer_fresh(RTMP_ADAPTER *ad){
 memset(&ad->MacTab,0,sizeof ad->MacTab);
 wr_iot_peer_table_owner_init(&ad->wr_iot_peer_table_owner);
 wr_iot_peer_close_executor_init(&ad->wr_iot_peer_close_executor);
 ad->wr_iot_peer_close_serial=0;ad->wr_iot_peer_legacy_close_state=0;ad->wr_iot_peer_delete_active=0;
}
'''
    if 'static int wr_iot_mgmt_exit_checked(' not in text:
        text+='static int wr_iot_mgmt_exit_checked(RTMP_ADAPTER *ad,const struct wr_iot_radio_ticket *t){assert(!held&&ad&&t);joins++;return join_result;}\n'
    return text

def fresh(text):
    return text.replace('wr_iot_radio_transition_init(&a.wr_iot_transition);',
                        'wr_test_peer_fresh(&a);wr_iot_radio_transition_init(&a.wr_iot_transition);')
