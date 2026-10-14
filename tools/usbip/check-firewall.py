#!/usr/bin/env python3
"""Run the actual policy functions with isolated command/network fixtures."""
import os
import subprocess
import tempfile
from pathlib import Path

source = Path(__file__).with_name('firewall-policy.sh').read_text()
with tempfile.TemporaryDirectory(prefix='wr-usbip-policy-') as directory:
    root = Path(directory)
    (root/'net/br0').mkdir(parents=True)
    binary = root/'bin'
    binary.mkdir()
    for name, body in {
        'iptables': 'test "${FAIL_LIST:-0}" = 0 || exit 1\nprintf "%s\\n" "${RULES:-}"\n',
        'iptables-restore': 'test "$1" = --noflush && test "$2" = --wait=5 || exit 3\ncat > "$CAPTURE"\nexit "${RESTORE_EXIT:-0}"\n',
    }.items():
        path = binary/name
        path.write_text('#!/bin/sh\n'+body)
        path.chmod(0o755)
    policy = root/'policy.sh'
    policy.write_text(source.replace('/sys/class/net/', str(root/'net')+'/'))
    capture = root/'rules'
    env = dict(os.environ, PATH=str(binary)+':'+os.environ['PATH'], CAPTURE=str(capture))

    def invoke(action, lan='br0', **extra):
        if capture.exists():
            capture.unlink()
        return subprocess.run(['sh','-c','. "$1"; "$2" "$3"','fixture',str(policy),action,lan],
                              env=dict(env,**extra),capture_output=True,text=True)

    assert invoke('wr_usbip_policy_apply').returncode == 0
    rules = capture.read_text().splitlines()
    assert rules == ['*filter', ':WRUSBIP_INPUT - [0:0]',
                     '-A WRUSBIP_INPUT -i lo -p tcp --dport 3240 -j ACCEPT',
                     '-A WRUSBIP_INPUT -i br0 -p tcp --dport 3240 -j ACCEPT',
                     '-A WRUSBIP_INPUT -p tcp --dport 3240 -j DROP',
                     '-A WRUSBIP_INPUT -j RETURN',
                     '-I INPUT 1 -j WRUSBIP_INPUT','COMMIT']
    hooks='-A INPUT -j WRUSBIP_INPUT\n-A INPUT -j OTHER\n-A INPUT -j WRUSBIP_INPUT'
    assert invoke('wr_usbip_policy_apply',RULES=hooks).returncode == 0
    assert capture.read_text().count('-D INPUT -j WRUSBIP_INPUT\n') == 2
    for invalid in ('', 'lo', 'missing', 'br0;reboot', 'a'*16):
        assert invoke('wr_usbip_policy_apply',invalid).returncode != 0
        assert not capture.exists()
    assert invoke('wr_usbip_policy_apply',FAIL_LIST='1').returncode != 0
    assert not capture.exists()
    assert invoke('wr_usbip_policy_apply',RESTORE_EXIT='1').returncode != 0
    assert invoke('wr_usbip_policy_remove',RULES=hooks).returncode == 0
    assert capture.read_text().splitlines() == ['*filter', ':WRUSBIP_INPUT - [0:0]',
        '-D INPUT -j WRUSBIP_INPUT','-D INPUT -j WRUSBIP_INPUT','COMMIT']
    assert invoke('wr_usbip_policy_apply',RULES='\n'.join(['-A INPUT -j WRUSBIP_INPUT']*33)).returncode != 0
    assert not capture.exists()
print('PASS USB/IP policy: LAN/loopback only, owned hooks, invalid input and command failures')
