#include <assert.h>
#include <stdio.h>
#include "plan.h"
int main(void)
{
    /* Pinned WR1200JS config, not measured physical socket identification. */
    struct wr_wan_port_board board = {0, {1,2,3,4}}, reversed = {4, {3,2,1,0}};
    struct wr_wan_port_plan plan;
    unsigned choice;
    for (choice = 0; choice < 5; choice++) {
        assert(wr_wan_port_plan(&board, choice, &plan));
        assert(plan.wan_phy == choice && plan.wan_external == (1U << choice));
        assert(plan.lan_external == (0x1eU & ~(1U << choice)));
        assert(plan.isolated_external == (choice ? 1U : 0U));
        assert(wr_wan_port_plan(&reversed, choice, &plan));
        assert(plan.wan_phy == 4-choice);
        assert((plan.wan_external | plan.lan_external | plan.isolated_external) == 0x1fU);
    }
    assert(!wr_wan_port_plan(&board, 5, &plan) && !plan.wan_external);
    board.lan[3] = board.original_wan;
    assert(!wr_wan_port_plan(&board, 0, &plan));
    board.lan[3] = 32;
    assert(!wr_wan_port_plan(&board, 0, &plan));
    assert(!wr_wan_port_plan(NULL, 0, &plan));
    assert(!wr_wan_port_plan(&reversed, 0, NULL));
    puts("PASS WAN external-port plan: original/each LAN, old-WAN isolation, reversed mapping and invalid maps");
    return 0;
}
