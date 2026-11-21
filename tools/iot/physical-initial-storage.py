"""Pure candidate storage/retirement transform; not installed by this module."""
def compose(header,initialization,raw_free):
    if 'wr_iot_physical_initial' in header or 'wr_iot_physical_initial' in raw_free:
        raise ValueError('Initial physical storage already present')
    def once(text,old,new):
        if text.count(old)!=1:raise ValueError('Initial storage anchor changed: '+old[:60])
        return text.replace(old,new,1)
    header=once(header,'#include "physical-stop-terminal-types.h"',
        '#include "physical-stop-terminal-types.h"\n#include "physical-initial-types.h"\n#include "physical-initial-terminal-types.h"')
    header=once(header,'struct wr_iot_physical_stop_terminal wr_iot_physical_terminal;',
        'struct wr_iot_physical_stop_terminal wr_iot_physical_terminal;\n struct wr_iot_physical_initial_record wr_iot_physical_initial;\n struct wr_iot_physical_initial_terminal wr_iot_physical_initial_terminal;')
    anchor='NdisZeroMemory(&pAd->wr_iot_physical_terminal,sizeof(pAd->wr_iot_physical_terminal));'
    initialization=once(initialization,anchor,anchor+'\n NdisZeroMemory(&pAd->wr_iot_physical_initial,sizeof(pAd->wr_iot_physical_initial));\n NdisZeroMemory(&pAd->wr_iot_physical_initial_terminal,sizeof(pAd->wr_iot_physical_initial_terminal));')
    raw_free=once(raw_free,'#include "physical-stop-terminal.inc"',
        '#include "physical-stop-terminal.inc"\n#include "physical-initial-terminal.inc"')
    raw_free=once(raw_free,'struct wr_iot_physical_stop_terminal terminal={0},empty={0};',
        'struct wr_iot_physical_stop_terminal terminal={0},empty={0};\n  struct wr_iot_physical_initial_terminal initial={0},initial_empty={0};')
    raw_free=once(raw_free,'ready=ad->wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE&&',
        'ready=!ad->wr_iot_physical_initial.task&&\n   (!ad->wr_iot_physical_initial.status||\n    (ad->wr_iot_physical_initial_terminal.owner&&ad->wr_iot_physical_initial_terminal.ready))&&\n   (!ad->wr_iot_physical_initial_terminal.owner||ad->wr_iot_physical_initial_terminal.ready)&&\n   ad->wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE&&')
    anchor='if(ready){terminal=ad->wr_iot_physical_terminal;ad->wr_iot_physical_terminal=empty;}'
    raw_free=once(raw_free,anchor,'if(ready){terminal=ad->wr_iot_physical_terminal;ad->wr_iot_physical_terminal=empty;\n   initial=ad->wr_iot_physical_initial_terminal;ad->wr_iot_physical_initial_terminal=initial_empty;}')
    raw_free=once(raw_free,'if(terminal.owner)wr_iot_physical_stop_terminal_clear(&terminal);',
        'if(terminal.owner)wr_iot_physical_stop_terminal_clear(&terminal);\n  if(initial.owner)wr_iot_physical_initial_terminal_clear(&initial);')
    return header,initialization,raw_free
