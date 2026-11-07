#!/usr/bin/env python3
"""Extract outer wrapper; compile with candidate include directory, not old headers."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'ap/ap_wds.c').read_text()
anchor='MAC_TABLE_ENTRY *MacTableInsertWDSEntry('
assert s.count(anchor)==1
start=s.index(anchor);end=s.index('\n}',start)+2;body=s[start:end]
for token in ['wr_iot_wds_peer_operation_enter(', 'wr_iot_radio_tx_enter(', 'wr_iot_radio_tx_leave(', 'dev_hold(', 'dev_put(',
              'result = wr_iot_wds_insert_body(', 'r->phase == WR_REF_OWNED']:
    assert body.count(token)==1,token
assert body.count('wr_iot_wds_peer_operation_leave(')==2
template=Path(__file__).with_name('wds-outer-operation-fixture.c.in').read_text()
marker='/* WR_IOT_EXTRACTED_OUTER_WRAPPER */';assert template.count(marker)==1
a.output.write_text(template.replace(marker,body),encoding='utf-8')
print('Extracted complete outer operation wrapper; vendor body/lifetime primitives mocked')
