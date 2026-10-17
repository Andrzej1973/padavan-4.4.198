#!/usr/bin/env python3
"""Exercise the apply controller order with fake controls; no system changes."""
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

HARNESS = '''#include "profile-apply.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static FILE *log_file;
static int calls, fail_at;

static int record(void *context,const char *const argv[])
{
    int i;
    (void)context;
    calls++;
    if (fail_at==calls) return 1;
    for (i=0;argv[i];i++) fprintf(log_file,"%s%s",i?" ":"",argv[i]);
    fputs("\\n",log_file);fflush(log_file);
    return 0;
}

static int make_session(const char *root,struct wr_vpn_session *out,enum wr_vpn_protocol protocol)
{
    struct wr_vpn_runtime runtime={-1,-1};
    struct wr_vpn_session intent,observed;
    if (!wr_vpn_session_new(&intent,2,protocol,5)) return 0;
    if (wr_vpn_runtime_lock(root,&runtime)!=WR_VPN_RUNTIME_OK) return 0;
    if (wr_vpn_runtime_put(&runtime,&intent,NULL)!=WR_VPN_RUNTIME_OK) return 0;
    observed=intent;observed.index=54;
    if (wr_vpn_runtime_put(&runtime,&observed,&intent)!=WR_VPN_RUNTIME_OK) return 0;
    wr_vpn_runtime_unlock(&runtime);
    *out=observed;
    return 1;
}

int main(int argc,char **argv)
{
    struct wr_vpn_record profile;struct wr_vpn_session expected;
    struct wr_vpn_apply_options options={NULL,0};struct wr_vpn_apply_outcome outcome;
    struct wr_vpn_exec exec={record,NULL};
    const char *prefixes[4];int count=0;char *text;
    if (argc!=5) return 99;
    log_file=fopen(argv[3],"w");if (!log_file) return 98;
    fail_at=atoi(argv[4]);
    memset(&profile,0,sizeof(profile));profile.id=2;
    profile.protocol=(enum wr_vpn_protocol)atoi(argv[2]);profile.revision=5;
    profile.size=fread(profile.config,1,sizeof(profile.config),stdin);
    if (!make_session(argv[1],&expected,profile.protocol)) return 96;
    text=getenv("PROTECT");
    while (text && *text && count<4) {
        char *comma=strchr(text,',');
        if (comma) *comma=0;
        prefixes[count++]=text;
        text=comma?comma+1:NULL;
    }
    options.protected_prefixes=count?prefixes:NULL;options.protected_count=(size_t)count;
    if (!wr_vpn_profile_apply(argv[1],&profile,&expected,&options,&exec,&outcome)) return 97;
    printf("%d,%d,%d,%d,%d,%d,%d\\n",(int)outcome.protocol,(int)outcome.addresses,
           (int)outcome.routes,outcome.addresses_attempted,outcome.routes_attempted,
           (int)outcome.dns,outcome.dns_attempted);
    fclose(log_file);
    return 0;
}
'''

CONTROL = '''#include <stdio.h>
#include <string.h>
int main(int argc,char **argv)
{
    char data[200000];size_t n;
    FILE *marker=fopen(MARKER,"a");
    if (marker) { fputs("called\\n",marker);fclose(marker); }
    if (VERIFY) {
        if (argc!=3 || strcmp(argv[1],"wrvpn2") || strcmp(argv[2],"54")) return 90;
    } else if (argc!=4 || strcmp(argv[1],"setconf") || strcmp(argv[2],"wrvpn2") ||
               strcmp(argv[3],"/proc/self/fd/0")) return 90;
    n=fread(data,1,sizeof(data),stdin);
    return n?0:0;
}
'''

with tempfile.TemporaryDirectory(prefix='wrvpn-controller-') as directory:
    root = Path(directory)
    harness = root / 'harness.c'
    harness.write_text(HARNESS)
    control = root / 'control.c'
    control.write_text(CONTROL)
    controls = {1: root / 'wg', 2: root / 'awg'}
    verifiers = {1: root / 'readback-wg', 2: root / 'readback-awg'}

    def compile_control(protocol, verify):
        subprocess.run(['gcc', '-Wall', '-Wextra', '-Werror',
                        f'-DVERIFY={int(verify)}',
                        f'-DMARKER="{root}/control-{protocol}-{int(verify)}.calls"',
                        str(control),
                        '-o', str((verifiers if verify else controls)[protocol])], check=True)

    for protocol in controls:
        compile_control(protocol, False)
        compile_control(protocol, True)

    exe = root / 'controller'
    subprocess.run(['gcc', '-std=gnu99', '-Wall', '-Wextra', '-Werror', '-g',
                    '-fsanitize=address,undefined', '-I' + str(here),
                    '-DWR_VPN_CONTROL_WG=' + json.dumps(str(controls[1])),
                    '-DWR_VPN_CONTROL_AWG=' + json.dumps(str(controls[2])),
                    '-DWR_VPN_READBACK_WG=' + json.dumps(str(verifiers[1])),
                    '-DWR_VPN_READBACK_AWG=' + json.dumps(str(verifiers[2])),
                    '-DWR_VPN_VALIDATE_WG=' + json.dumps(str(args.wg_validator.resolve())),
                    '-DWR_VPN_VALIDATE_AWG=' + json.dumps(str(args.awg_validator.resolve())),
                    '-DWR_VPN_APPLY_TIMEOUT_MS=300', str(harness),
                    str(here / 'profile-apply.c'), str(here / 'addr-apply.c'),
                    str(here / 'route-apply.c'), str(here / 'dns-apply.c'),
                    str(here / 'config-transaction.c'),
                    str(here / 'config-apply.c'), str(here / 'config-plan.c'),
                    str(here / 'validate-process.c'), str(here / 'runtime-state.c'),
                    '-o', str(exe)], check=True)

    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:exitcode=98',
               UBSAN_OPTIONS='halt_on_error=1:exitcode=97')
    counter = 0

    def run(protocol, protect, data, fail_at=0):
        global counter
        counter += 1
        runtime = root / f'runtime-{counter}'
        runtime.mkdir(mode=0o700)
        log = runtime / 'commands'
        run_env = dict(env)
        if protect:
            run_env['PROTECT'] = protect
        else:
            run_env.pop('PROTECT', None)
        result = subprocess.run([str(exe), str(runtime), str(protocol), str(log), str(fail_at)],
                                input=data.encode(), capture_output=True, timeout=20, env=run_env)
        assert result.returncode == 0 and not result.stderr, (result.returncode, result.stderr)
        commands = log.read_text().splitlines() if log.exists() else []
        return result.stdout.decode().strip(), commands

    for protocol in controls:
        data = config if protocol == 1 else config.replace('[Peer]', 'Jc = 4\n[Peer]')

        outcome, commands = run(protocol, '192.168.20.0/24', data)
        assert outcome == '0,0,0,1,1,0,1', (outcome, commands)
        assert commands == ['ip address add 10.8.0.2/32 dev wrvpn2',
                            'ip route replace 0.0.0.0/0 dev wrvpn2 table 20002',
                            'ip rule add fwmark 0x57560002/0xffffffff lookup 20002 priority 20003'], commands

        # No protected prefix: refuse before the protocol transport runs.
        for other in controls:
            for verify in (0, 1):
                (root / f'control-{other}-{verify}.calls').unlink(missing_ok=True)
        outcome, commands = run(protocol, None, data)
        assert outcome == '4,2,1,1,0,1,0', (outcome, commands)
        assert commands == [], commands
        for verify in (0, 1):
            assert not (root / f'control-{protocol}-{verify}.calls').exists(), \
                'protocol transport ran without a protected prefix'

        outcome, commands = run(protocol, '192.168.20.0/24', data, fail_at=2)
        assert outcome == '0,0,3,1,1,1,0', (outcome, commands)
        assert commands == ['ip address add 10.8.0.2/32 dev wrvpn2'], commands

    print('PASS apply controller: protocol, then addresses, then routes; no protected '
          'prefix refuses before the protocol transport; a failing runner stops the '
          'sequence and reports it')
