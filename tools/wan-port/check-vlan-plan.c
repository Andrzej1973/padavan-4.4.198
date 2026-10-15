#include <assert.h>
#include <stdio.h>
#include "vlan-plan.h"
int main(void)
{
    struct wr_wan_port_board board = {0,{1,2,3,4}};
    struct wr_wan_vlan_table base = {.count=4};
    struct wr_wan_vlan_result result;
    unsigned choice, i;
    base.entries[0] = (struct wr_wan_vlan_entry){1,1,0x5e,0x5e,0}; /* LAN + CPU6 */
    base.entries[1] = (struct wr_wan_vlan_entry){1,2,0x21,0x21,0}; /* WAN + CPU5 */
    base.entries[2] = (struct wr_wan_vlan_entry){1,100,0x21,0,0}; /* tagged INET */
    base.entries[3] = (struct wr_wan_vlan_entry){1,200,0x21,0,1}; /* WAN VID translation */
    base.pvid[0]=2; for(i=1;i<5;i++)base.pvid[i]=1;
    for(choice=0;choice<5;choice++) {
        uint32_t selected=1U<<choice;
        assert(wr_wan_vlan_plan(&board,choice,0x40,0x20,1,&base,&result)==WR_WAN_VLAN_OK);
        if(!choice){assert(!memcmp(&base,&result.table,sizeof(base)));continue;}
        assert(result.table.entries[0].members==(0x5eU&~selected));
        assert(result.table.entries[1].members==(0x20U|selected));
        assert(result.table.entries[1].untag==(0x20U|selected));
        assert(result.table.entries[2].members==(0x20U|selected) && !result.table.entries[2].untag);
        assert(result.table.entries[3].swap==selected);
        assert(result.table.pvid[choice]==2 && result.ports.isolated_external==1);
        for(i=0;i<base.count;i++)assert(!(result.table.entries[i].members&1));
    }
    /* IPTV on a different LAN remains intact; stealing its socket refuses. */
    base.entries[0].members &= ~16U; base.entries[0].untag &= ~16U;
    base.entries[3].members |= 16U; base.entries[3].untag |= 16U; base.pvid[4]=200;
    assert(wr_wan_vlan_plan(&board,1,0x40,0x20,1,&base,&result)==WR_WAN_VLAN_OK);
    assert((result.table.entries[3].members&16U) && (result.table.entries[3].untag&16U));
    assert(result.reserved_external==16U && result.lan_members_external==(0x0eU&~2U));
    assert(wr_wan_vlan_plan(&board,4,0x40,0x20,1,&base,&result)==WR_WAN_VLAN_CONFLICT);
    assert(!result.table.count);
    assert(wr_wan_vlan_plan(&board,1,1,0x20,1,&base,&result)==WR_WAN_VLAN_INVALID);
    base.entries[0].members |= 1U;
    assert(wr_wan_vlan_plan(&board,1,0x40,0x20,1,&base,&result)==WR_WAN_VLAN_CONFLICT);
    base.entries[0].members &= ~1U;
    base.entries[2].vid=2;
    assert(wr_wan_vlan_plan(&board,1,0x40,0x20,1,&base,&result)==WR_WAN_VLAN_INVALID);
    puts("PASS WAN VLAN plan: CPU/remaining-LAN preservation, tagged rules, PVID and IPTV conflicts");
    return 0;
}
