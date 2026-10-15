#!/usr/bin/env python3
"""Parse actual fixture HTTP output with an independent JSON implementation."""
import json
import subprocess
import sys
reply = json.loads(subprocess.check_output([sys.argv[1], '--json'], text=True, timeout=15))
assert reply['schema'] == 1 and reply['master'] == '1'
assert len(reply['slots']) == 8
for slot, row in enumerate(reply['slots']):
    assert row['slot'] == slot
    for key in ('enable','autostart','local','remote','id','mtu','keepalive','retries','bridge'):
        assert row[key] == r'"quoted\value'
print('PASS actual EoIP HTTP fixture JSON: eight slots and quote/backslash roundtrip')
