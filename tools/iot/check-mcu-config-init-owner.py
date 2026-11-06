#!/usr/bin/env python3
"""Check outer-init config ownership ordering and preserved admission refusal."""
import argparse
from pathlib import Path
import re

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
a = p.parse_args()
source = (a.candidate / 'common/rtmp_init_inf.c').read_text()
start = source.index('int rt28xx_init(')
body = source[start:source.index('\nVOID RTMPDrvOpen(', start)]
begin = 'wr_iot_mcu_boot_config_begin(pAd,&wr_config_ticket)'
finish = 'wr_iot_mcu_boot_config_finish(pAd,&wr_config_ticket,1)'
abandon = 'wr_iot_mcu_boot_config_finish(pAd,&wr_config_ticket,0)'
assert body.count(begin) == 1 and body.count(finish) == 1 and body.count(abandon) == 1
assert body.index('MCUSysInit(pAd)') < body.index(begin) < body.index('RtmpChipOpsEepromHook')
assert body.index(finish) < body.index('DBGPRINT_S(("<==== rt28xx_init')
success = body[body.index(finish):body.index('DBGPRINT_S(("<==== rt28xx_init')]
assert 'goto err8;' in success and 'Normal command/data admission remains separately closed.' in success
err6_tail = body[body.index('err6:'):]
assert body.index('err6:') < body.index(abandon)
assert 'MCUSysExit' in err6_tail and err6_tail.index(abandon) < err6_tail.index('MCUSysExit')
assert 'if(wr_config_started)' in err6_tail[:err6_tail.index('MCUSysExit')]
for action in ('RTMP_IRQ_ENABLE(pAd);', 'RTMPEnableRxTx(pAd);'):
    sites = list(re.finditer(re.escape(action), body))
    assert sites, action
    for site in sites:
        prefix = body[:site.start()].rstrip()
        assert prefix.endswith('if(wr_config_started)goto err8;\n#endif'), action
print('PASS outer config owner: begin after MCUSysInit, every later error reaches abandon, success stays refused before normal admission; source ordering only')
