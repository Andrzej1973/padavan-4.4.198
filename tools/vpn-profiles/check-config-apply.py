#!/usr/bin/env python3
"""Exercise apply transport with real validators and fake controls; no network changes."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--wg-validator', required=True, type=Path)
p.add_argument('--awg-validator', required=True, type=Path)
a = p.parse_args()
here = Path(__file__).resolve().parent
key = base64.b64encode(bytes(range(1, 33))).decode()
public = base64.b64encode(bytes(range(33, 65))).decode()
config = f'[Interface]\nPrivateKey = {key}\nAddress = 10.8.0.2/32\n[Peer]\nPublicKey = {public}\nEndpoint = 203.0.113.7:51820\nAllowedIPs = 0.0.0.0/0\n'
with tempfile.TemporaryDirectory(prefix='wrvpn-apply-') as directory:
    root = Path(directory)
    harness = root / 'harness.c'
    harness.write_text('''#include "config-apply.h"
#include <stdlib.h>
int main(int argc,char **argv) {
    struct wr_vpn_record r;memset(&r,0,sizeof(r));
    if(argc!=2 && argc!=3)return 99;
    r.id=2;r.revision=1;r.protocol=atoi(argv[1]);
    r.size=fread(r.config,1,sizeof(r.config),stdin);
    printf("%d\\n",argc==3?(int)wr_vpn_config_readback(&r,54):(int)wr_vpn_config_apply(&r));return 0;
}
''')
    control = root / 'control.c'
    control.write_text('''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
extern char **environ;
int main(int argc,char **argv) {
    char data[200000];struct stat s;FILE *f;size_t n;int fd;
    if(VERIFY) {
        if(argc!=3 || strcmp(argv[1],"wrvpn2") || strcmp(argv[2],"54"))return 90;
    } else if(argc!=4 || strcmp(argv[1],"setconf") || strcmp(argv[2],"wrvpn2") ||
       strcmp(argv[3],"/proc/self/fd/0"))return 90;
    if(!environ[0] || strcmp(environ[0],"LC_ALL=C") || environ[1])return 91;
    for(fd=3;fd<4096;fd++)if(fcntl(fd,F_GETFD)!=-1 || errno!=EBADF)return 92;
    if(fstat(0,&s) || !S_ISREG(s.st_mode) || s.st_nlink || (s.st_mode&0777)!=0600)return 93;
    f=fopen("/proc/self/fd/0","r");if(!f)return 94;
    n=fread(data,1,sizeof(data)-1,f);data[n]=0;fclose(f);
    if(!strstr(data,"PrivateKey = ") || !strstr(data,"FwMark = ") ||
       strstr(data,"Address = ") || (!!strstr(data,"Jc = ")!=AWG))return 95;
    f=fopen(MARKER,"a");if(!f)return 96;fputs("called\\n",f);fclose(f);
    puts(data);fputs(data,stderr); /* must be suppressed by transport */
    if(MODE==1)sleep(10);
    return MODE==2?(VERIFY?2:7):(MODE==3?7:0);
}
''')
    controls = {1: root / 'wg', 2: root / 'awg'}
    verifiers = {1: root / 'readback-wg', 2: root / 'readback-awg'}
    marker = root / 'called'
    def compile_control(protocol, mode=0, verify=False):
        subprocess.run(['gcc', '-Wall', '-Wextra', '-Werror',
                        f'-DAWG={int(protocol == 2)}', f'-DMODE={mode}', f'-DVERIFY={int(verify)}',
                        '-DMARKER=' + json.dumps(str(marker)), str(control),
                        '-o', str((verifiers if verify else controls)[protocol])], check=True)
    for protocol in controls:
        compile_control(protocol)
    exe = root / 'apply'
    subprocess.run(['gcc', '-std=gnu99', '-Wall', '-Wextra', '-Werror',
                    '-g', '-fsanitize=address,undefined', '-I' + str(here),
                    '-DWR_VPN_CONTROL_WG=' + json.dumps(str(controls[1])),
                    '-DWR_VPN_CONTROL_AWG=' + json.dumps(str(controls[2])),
                    '-DWR_VPN_READBACK_WG=' + json.dumps(str(verifiers[1])),
                    '-DWR_VPN_READBACK_AWG=' + json.dumps(str(verifiers[2])),
                    '-DWR_VPN_VALIDATE_WG=' + json.dumps(str(a.wg_validator.resolve())),
                    '-DWR_VPN_VALIDATE_AWG=' + json.dumps(str(a.awg_validator.resolve())),
                    '-DWR_VPN_APPLY_TIMEOUT_MS=300', str(harness),
                    str(here / 'config-apply.c'), str(here / 'config-plan.c'),
                    str(here / 'validate-process.c'), '-o', str(exe)], check=True)
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:exitcode=98',
               UBSAN_OPTIONS='halt_on_error=1:exitcode=97', MUST_NOT_LEAK='secret')
    def run(protocol, data, expected, verify=False):
        with (root / 'private-fd').open('w+') as extra:
            r = subprocess.run([str(exe), str(protocol), *(['verify'] if verify else [])], input=data.encode(),
                               capture_output=True, timeout=8, env=env,
                               pass_fds=(extra.fileno(),))
        assert r.returncode == 0 and not r.stderr, (r.returncode, r.stderr)
        assert r.stdout == f'{expected}\n'.encode(), r.stdout
    for protocol in controls:
        data = config if protocol == 1 else config.replace('[Peer]', 'Jc = 4\n[Peer]')
        run(protocol, data, 3)  # only command acknowledgement
        before = marker.read_bytes()
        run(protocol, data.replace('203.0.113.7', 'test.invalid'), 0)
        run(protocol, data.replace(key, 'invalid'), 0)
        run(protocol, data.replace('[Peer]', 'PreUp = never\n[Peer]'), 0)
        assert marker.read_bytes() == before
        compile_control(protocol, 2)
        run(protocol, data, 2)
        compile_control(protocol, 1)
        began = time.monotonic()
        run(protocol, data, 2)
        assert time.monotonic() - began < 5
        controls[protocol].unlink()
        run(protocol, data, 2)
        for mode, expected in [(0, 2), (2, 1), (3, 0), (1, 0)]:
            compile_control(protocol, mode, verify=True)
            run(protocol, data, expected, verify=True)
        verifiers[protocol].unlink()
        run(protocol, data, 0, verify=True)
    print('PASS apply transport: fixed protocol argv, unlinked private input, FD/env isolation, secret output suppression, rejection, failure/timeout; no kernel configuration proof')
