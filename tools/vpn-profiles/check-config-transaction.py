#!/usr/bin/env python3
"""Exercise the config transaction with real runtime bookkeeping and fake
controls; no kernel or network changes."""
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
config = (f'[Interface]\nPrivateKey = {key}\nAddress = 10.8.0.2/32\n'
          f'[Peer]\nPublicKey = {public}\nEndpoint = 203.0.113.7:51820\n'
          'AllowedIPs = 0.0.0.0/0\n')

HARNESS = '''#include "config-transaction.h"
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/file.h>
#include <unistd.h>

static int make_session(const char *root,unsigned int id,enum wr_vpn_protocol protocol,
                        struct wr_vpn_session *out)
{
    struct wr_vpn_runtime runtime={-1,-1};
    struct wr_vpn_session intent,observed;
    enum wr_vpn_runtime_result status;
    if (wr_vpn_runtime_lock(root,&runtime)!=WR_VPN_RUNTIME_OK) return 0;
    status=wr_vpn_runtime_read(&runtime,id,out);
    if (status==WR_VPN_RUNTIME_OK) { wr_vpn_runtime_unlock(&runtime);return 1; }
    if (status!=WR_VPN_RUNTIME_ABSENT) { wr_vpn_runtime_unlock(&runtime);return 0; }
    if (!wr_vpn_session_new(&intent,id,protocol,5)) { wr_vpn_runtime_unlock(&runtime);return 0; }
    if (wr_vpn_runtime_put(&runtime,&intent,NULL)!=WR_VPN_RUNTIME_OK) {
        wr_vpn_runtime_unlock(&runtime);return 0;
    }
    observed=intent;observed.index=54;
    if (wr_vpn_runtime_put(&runtime,&observed,&intent)!=WR_VPN_RUNTIME_OK) {
        wr_vpn_runtime_unlock(&runtime);return 0;
    }
    wr_vpn_runtime_unlock(&runtime);
    *out=observed;
    return 1;
}

int main(int argc,char **argv)
{
    struct wr_vpn_record record,rollback;
    struct wr_vpn_session expected;
    const char *root,*scenario;
    enum wr_vpn_protocol protocol;
    int status;size_t size;char path[512];int lock;
    if (argc!=4) return 99;
    root=argv[1];protocol=(enum wr_vpn_protocol)atoi(argv[2]);scenario=argv[3];
    memset(&record,0,sizeof(record));record.id=2;record.protocol=protocol;record.revision=5;
    size=fread(record.config,1,sizeof(record.config),stdin);record.size=size;
    rollback=record;
    memset(&expected,0,sizeof(expected));
    expected.id=2;expected.protocol=protocol;expected.revision=5;expected.index=54;
    memset(expected.nonce,0x11,sizeof(expected.nonce));
    if (strcmp(scenario,"nosession") && !make_session(root,2,protocol,&expected)) return 98;
    if (!strcmp(scenario,"stale")) expected.nonce[0]^=1;
    if (!strcmp(scenario,"busy")) {
        snprintf(path,sizeof(path),"%s/.operation-lock",root);
        lock=open(path,O_RDWR|O_CREAT|O_CLOEXEC,0600);
        if (lock<0 || flock(lock,LOCK_EX|LOCK_NB)) return 97;
        status=(int)wr_vpn_config_transaction(root,&record,&expected,NULL);
        flock(lock,LOCK_UN);close(lock);
    } else if (!strcmp(scenario,"rollback")) {
        status=(int)wr_vpn_config_transaction(root,&record,&expected,&rollback);
    } else {
        status=(int)wr_vpn_config_transaction(root,&record,&expected,NULL);
    }
    printf("%d\\n",status);
    return 0;
}
'''

CONTROL = '''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
extern char **environ;
int main(int argc,char **argv)
{
    char data[200000];struct stat s;FILE *f,*counts;size_t n;int fd,first;
    if (VERIFY) {
        if (argc!=3 || strcmp(argv[1],"wrvpn2") || strcmp(argv[2],"54")) return 90;
    } else if (argc!=4 || strcmp(argv[1],"setconf") || strcmp(argv[2],"wrvpn2") ||
               strcmp(argv[3],"/proc/self/fd/0")) return 90;
    if (!environ[0] || strcmp(environ[0],"LC_ALL=C") || environ[1]) return 91;
    for (fd=3;fd<4096;fd++) if (fcntl(fd,F_GETFD)!=-1) return 92;
    if (fstat(0,&s) || !S_ISREG(s.st_mode) || s.st_nlink || (s.st_mode&0777)!=0600) return 93;
    f=fopen("/proc/self/fd/0","r");if (!f) return 94;
    n=fread(data,1,sizeof(data)-1,f);data[n]=0;fclose(f);
    if (!strstr(data,"PrivateKey = ") || strstr(data,"Address = ") ||
        (!!strstr(data,"Jc = ")!=AWG)) return 95;
    f=fopen(MARKER,"a");if (!f) return 96;
    fputs(VERIFY?"verify\\n":"apply\\n",f);fclose(f);
    if (!VERIFY) return MODE==3?7:0;
    if (MODE==2) return 2;
    if (MODE==4) {
        first=1;counts=fopen(COUNT,"r");
        if (counts) { first=0;fclose(counts); }
        counts=fopen(COUNT,"w");if (!counts) return 96;
        fputs("seen\\n",counts);fclose(counts);
        return first?2:0;
    }
    return 0;
}
'''

with tempfile.TemporaryDirectory(prefix='wrvpn-transaction-') as directory:
    temporary = Path(directory)
    harness = temporary / 'harness.c'
    harness.write_text(HARNESS)
    control = temporary / 'control.c'
    control.write_text(CONTROL)

    marker = temporary / 'calls'
    count = temporary / 'count'
    controls = {1: temporary / 'wg', 2: temporary / 'awg'}
    verifiers = {1: temporary / 'readback-wg', 2: temporary / 'readback-awg'}

    def compile_control(protocol, mode=0, verify=False):
        subprocess.run(['gcc', '-Wall', '-Wextra', '-Werror',
                        f'-DAWG={int(protocol == 2)}', f'-DMODE={mode}',
                        f'-DVERIFY={int(verify)}',
                        '-DMARKER=' + json.dumps(str(marker)),
                        '-DCOUNT=' + json.dumps(str(count)),
                        str(control),
                        '-o', str((verifiers if verify else controls)[protocol])],
                       check=True)

    exe = temporary / 'transaction'
    subprocess.run(['gcc', '-std=gnu99', '-Wall', '-Wextra', '-Werror',
                    '-g', '-fsanitize=address,undefined', '-I' + str(here),
                    '-DWR_VPN_CONTROL_WG=' + json.dumps(str(controls[1])),
                    '-DWR_VPN_CONTROL_AWG=' + json.dumps(str(controls[2])),
                    '-DWR_VPN_READBACK_WG=' + json.dumps(str(verifiers[1])),
                    '-DWR_VPN_READBACK_AWG=' + json.dumps(str(verifiers[2])),
                    '-DWR_VPN_VALIDATE_WG=' + json.dumps(str(args.wg_validator.resolve())),
                    '-DWR_VPN_VALIDATE_AWG=' + json.dumps(str(args.awg_validator.resolve())),
                    '-DWR_VPN_APPLY_TIMEOUT_MS=300', str(harness),
                    str(here / 'config-transaction.c'), str(here / 'config-apply.c'),
                    str(here / 'config-plan.c'), str(here / 'validate-process.c'),
                    str(here / 'runtime-state.c'), '-o', str(exe)], check=True)

    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:exitcode=98',
               UBSAN_OPTIONS='halt_on_error=1:exitcode=97')

    def run(root, protocol, scenario, data, expected, apply_mode=0, verify_mode=0):
        compile_control(protocol, apply_mode)
        compile_control(protocol, verify_mode, verify=True)
        for stale_file in (marker, count):
            if stale_file.exists():
                stale_file.unlink()
        result = subprocess.run([str(exe), str(root), str(protocol), scenario],
                                input=data.encode(), capture_output=True, timeout=20,
                                env=env)
        assert result.returncode == 0 and not result.stderr, (result.returncode, result.stderr)
        assert result.stdout == f'{expected}\n'.encode(), (scenario, result.stdout)
        return marker.read_text().splitlines() if marker.exists() else []

    counter = 0

    def fresh_root():
        global counter
        counter += 1
        path = temporary / f'profile-{counter}'
        path.mkdir(mode=0o700)
        return path

    for protocol in controls:
        data = config if protocol == 1 else config.replace('[Peer]', 'Jc = 4\n[Peer]')

        assert run(fresh_root(), protocol, 'nosession', data, 1) == []
        assert run(fresh_root(), protocol, 'busy', data, 2) == []
        assert run(fresh_root(), protocol, 'stale', data, 3) == []
        assert run(fresh_root(), protocol, 'plain', data.replace(key, 'invalid'), 4) == []
        assert run(fresh_root(), protocol, 'plain', data, 5, apply_mode=3) == ['apply']

        done_root = fresh_root()
        session_file = done_root / '2'
        calls = run(done_root, protocol, 'plain', data, 0)
        assert calls == ['apply', 'verify'], calls
        before = session_file.read_bytes()
        calls = run(done_root, protocol, 'plain', data, 0)
        assert calls == ['apply', 'verify'], calls
        assert session_file.read_bytes() == before

        calls = run(fresh_root(), protocol, 'rollback', data, 6, verify_mode=4)
        assert calls.count('apply') == 2 and calls.count('verify') == 2, calls

        calls = run(fresh_root(), protocol, 'rollback', data, 7, verify_mode=2)
        assert calls.count('apply') == 2 and calls.count('verify') == 2, calls

    print('PASS config transaction: lock, session CAS, refusal, unknown transport, '
          'verified apply, mismatch rollback and failed rollback; no kernel proof')
