#!/usr/bin/env python3
"""Exercise the secret-free apply preview with real validators; no network changes."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--wg-validator', required=True, type=Path)
parser.add_argument('--awg-validator', required=True, type=Path)
args = parser.parse_args()
here = Path(__file__).resolve().parent

key = base64.b64encode(bytes(range(1, 33))).decode()
public = base64.b64encode(bytes(range(33, 65))).decode()
config = (f'[Interface]\nPrivateKey = {key}\nAddress = 10.8.0.2/32\nDNS = 1.1.1.1\n'
          f'MTU = 1420\n[Peer]\nPublicKey = {public}\nEndpoint = 203.0.113.7:51820\n'
          'AllowedIPs = 0.0.0.0/0\n')

HARNESS = '''#include "plan-report.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int main(int argc,char **argv)
{
    struct wr_vpn_record record,snapshot;struct wr_vpn_session session;
    struct wr_vpn_session *observed=NULL;struct wr_vpn_record *rollback=NULL;
    static char out[40000];const char *scenario;
    if (argc!=3) return 99;
    scenario=argv[2];
    memset(&record,0,sizeof(record));record.id=2;
    record.protocol=(enum wr_vpn_protocol)atoi(argv[1]);record.revision=5;
    record.size=fread(record.config,1,sizeof(record.config),stdin);
    memset(&session,0,sizeof(session));session.id=2;session.protocol=record.protocol;
    session.revision=5;session.index=54;memset(session.nonce,0x22,sizeof(session.nonce));
    memset(&snapshot,0,sizeof(snapshot));snapshot.id=2;snapshot.protocol=record.protocol;
    snapshot.revision=4;snapshot.size=3;memcpy(snapshot.config,"old",3);
    if (!strcmp(scenario,"session") || !strcmp(scenario,"snapshot")) observed=&session;
    if (!strcmp(scenario,"stale")) { session.revision=4;observed=&session; }
    if (!strcmp(scenario,"snapshot")) rollback=&snapshot;
    if (!wr_vpn_plan_report(&record,observed,rollback,out,sizeof(out))) return 98;
    fputs(out,stdout);return 0;
}
'''

with tempfile.TemporaryDirectory(prefix='wrvpn-report-') as directory:
    root = Path(directory)
    harness = root / 'harness.c'
    harness.write_text(HARNESS)
    exe = root / 'report'
    subprocess.run(['gcc', '-std=gnu99', '-Wall', '-Wextra', '-Werror', '-g',
                    '-fsanitize=address,undefined', '-I' + str(here),
                    '-DWR_VPN_VALIDATE_WG=' + json.dumps(str(args.wg_validator.resolve())),
                    '-DWR_VPN_VALIDATE_AWG=' + json.dumps(str(args.awg_validator.resolve())),
                    str(harness), str(here / 'plan-report.c'), str(here / 'config-plan.c'),
                    str(here / 'validate-process.c'), str(here / 'store.c'),
                    '-o', str(exe)], check=True)

    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:exitcode=98',
               UBSAN_OPTIONS='halt_on_error=1:exitcode=97')

    def run(protocol, scenario, data):
        result = subprocess.run([str(exe), str(protocol), scenario], input=data.encode(),
                                capture_output=True, timeout=20, env=env)
        assert result.returncode == 0 and not result.stderr, (result.returncode, result.stderr)
        return result.stdout.decode()

    for protocol in (1, 2):
        data = config if protocol == 1 else config.replace('[Peer]', 'Jc = 4\n[Peer]')

        text = run(protocol, 'none', data)
        assert 'apply=no-session' in text and 'session=absent' in text, text
        assert 'snapshot=absent' in text and 'endpoints=numeric' in text, text
        assert 'addresses=10.8.0.2/32' in text and 'dns=1.1.1.1' in text, text
        assert 'mtu=1420' in text, text
        assert key not in text and public not in text, text

        text = run(protocol, 'session', data)
        assert 'apply=ready' in text and 'session=index=54,revision=5' in text, text

        text = run(protocol, 'stale', data)
        assert 'apply=stale' in text, text

        text = run(protocol, 'snapshot', data)
        assert 'apply=ready' in text and 'snapshot=revision=4' in text, text

        text = run(protocol, 'none', data.replace('203.0.113.7', 'vpn.example'))
        assert 'endpoints=hostname' in text and 'apply=needs-pinning' in text, text

        text = run(protocol, 'none', data.replace(key, 'invalid'))
        assert 'apply=invalid' in text and 'validation=rejected' in text, text

    print('PASS apply preview: requested fields, observed session and snapshot, '
          'ready/stale/needs-pinning/invalid states, and no key material in the output')
