#!/usr/bin/env python3
"""Check readback using pinned native parsers/IPC and synthetic observed devices."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--wg-source', required=True, type=Path)
p.add_argument('--awg-source', required=True, type=Path)
a = p.parse_args()
here = Path(__file__).resolve().parent
key = base64.b64encode(bytes(range(1, 33))).decode()
public = base64.b64encode(bytes(range(33, 65))).decode()
other = base64.b64encode(bytes(range(65, 97))).decode()
base = f'[Interface]\nPrivateKey = {key}\nFwMark = 1465253890\nListenPort = 51820\n[Peer]\nPublicKey = {public}\nAllowedIPs = 10.4.0.7/24, 2001:db8::9/64\nEndpoint = 203.0.113.7:51820\nPersistentKeepalive = 25\n'
env = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:exitcode=98',
           UBSAN_OPTIONS='halt_on_error=1:exitcode=97')
with tempfile.TemporaryDirectory(prefix='wrvpn-readback-') as directory:
    root = Path(directory)
    observed = root / 'observed.conf'
    stub = root / 'ipc-stub.c'
    stub.write_text('''#include <stdio.h>
#include <string.h>
#include "config.h"
#include "containers.h"
int __wrap_ipc_get_device(struct wgdevice **out,const char *name) {
    struct config_ctx ctx={0};char line[33000];FILE *f=fopen(OBSERVED,"r");
    if(!f)return -1;
    if(!config_read_init(&ctx,0)){fclose(f);return -1;}
    while(fgets(line,sizeof(line),f))if(!config_read_line(&ctx,line)){fclose(f);return -1;}
    fclose(f);*out=config_read_finish(&ctx);if(!*out)return -1;
    (*out)->ifindex=54;snprintf((*out)->name,sizeof((*out)->name),"%s",name);
    return 0;
}
''')
    for protocol, source, commit in [
        ('wg', a.wg_source, '3ba6527130c502144e7388b900138bca6260f4e8'),
        ('awg', a.awg_source, 'ee0f0a9aa34ff0a0da4b3433b9512781cfe02843'),
    ]:
        assert subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() == commit
        src = source.resolve() / 'src'
        flags = ['-std=gnu99', '-D_GNU_SOURCE', '-Wall', '-Wextra', '-g',
                 '-fsanitize=address,undefined', '-I' + str(src), '-I' + str(here)]
        flags += ['-idirafter', str(src / 'uapi/linux')] if protocol == 'wg' else ['-I' + str(src / 'uapi/linux'), '-DWR_VPN_NATIVE_AWG']
        units = [here / 'config-readback.c', src / 'config.c', src / 'encoding.c', src / 'ipc.c']
        if protocol == 'awg':
            units.append(src / 'type.c')
        objects = []
        for i, unit in enumerate(units):
            obj = root / f'{protocol}-{i}.o'
            subprocess.run(['gcc', *flags, *(['-Werror'] if unit == units[0] else []),
                            '-c', str(unit), '-o', str(obj)], check=True)
            objects.append(str(obj))
        native = root / f'native-{protocol}'
        subprocess.run(['gcc', '-fsanitize=address,undefined', *objects,
                        '-Wl,--wrap=getaddrinfo', '-o', str(native)], check=True)
        fake = root / f'fake-{protocol}'
        subprocess.run(['gcc', *flags, '-Werror', '-DOBSERVED=' + json.dumps(str(observed)),
                        str(stub), *objects, '-Wl,--wrap=getaddrinfo',
                        '-Wl,--wrap=ipc_get_device', '-o', str(fake)], check=True)
        wanted = base if protocol == 'wg' else base.replace('[Peer]', 'Jc = 4\nH1 = 100-200\n[Peer]')
        def run(exe, data, expected, interface='wrvpn2', index='54'):
            result = subprocess.run([str(exe), interface, index], input=data.encode(),
                                    capture_output=True, timeout=10, env=env)
            assert result.returncode == expected, (protocol, expected, result.returncode, result.stderr)
            assert not result.stdout and not result.stderr
        # Actual native IPC against a missing interface: unknown, never matched.
        run(native, wanted, 3, interface='wrvpn999')
        observed.write_text(wanted)
        run(fake, wanted, 0)
        run(fake, wanted, 3, index='55')
        run(fake, wanted, 3, interface='wg0')
        run(fake, wanted.replace('203.0.113.7', 'must-not-resolve.invalid'), 3)
        for old, new in [(key, other), ('1465253890', '51'), ('51820\n[Peer]', '51821\n[Peer]'),
                         (public, other), ('203.0.113.7', '203.0.113.8'),
                         ('PersistentKeepalive = 25', 'PersistentKeepalive = 26'),
                         ('10.4.0.7/24', '10.5.0.0/24'), ('2001:db8::9/64', '2001:db9::/64')]:
            observed.write_text(wanted.replace(old, new))
            run(fake, wanted, 2)
        observed.write_text(wanted.replace('10.4.0.7/24, 2001:db8::9/64', '2001:db8::/64, 10.4.0.0/24'))
        run(fake, wanted, 0)  # kernel masks host bits and may reorder prefixes
        observed.write_text(wanted + f'[Peer]\nPublicKey = {other}\nAllowedIPs = 10.6.0.0/24\n')
        run(fake, wanted, 2)
        observed.write_text(wanted.replace('[Peer]', f'[Peer]\nPresharedKey = {other}'))
        run(fake, wanted, 2)
        if protocol == 'awg':
            for old, new in [('Jc = 4', 'Jc = 5'), ('H1 = 100-200', 'H1 = 100-201'), ('H1 = 100-200\n', '')]:
                observed.write_text(wanted.replace(old, new))
                run(fake, wanted, 2)
        observed.unlink()
        run(fake, wanted, 3)
        print(f'PASS {protocol} readback: pinned native parser/IPC compilation, missing real device unknown, synthetic match/drift/index/peer/prefix/secret gates; no physical acceptance')
