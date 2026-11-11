#!/usr/bin/env python3
"""Bounded, read-only CI network probes; no credentials or environment dump."""
import json
import os
from pathlib import Path
import subprocess
import time

HOSTS = ('archive.ubuntu.com', 'security.ubuntu.com', 'azure.archive.ubuntu.com',
         'github.com', 'packages.microsoft.com')

def probe(argv, timeout=9):
    started = time.monotonic()
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
        return dict(code=result.returncode, seconds=round(time.monotonic()-started, 2),
                    stdout=result.stdout[-3000:], stderr=result.stderr[-1000:])
    except subprocess.TimeoutExpired:
        return dict(code=None, seconds=round(time.monotonic()-started, 2), error='timeout')
    except OSError as exc:
        return dict(code=None, error=type(exc).__name__)

def main():
    from concurrent.futures import ThreadPoolExecutor
    report = {'proxy_present': {k: bool(os.environ.get(k)) for k in
              ('http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY')},
              'resolver': {}, 'hosts': {}}
    for name in ('/etc/resolv.conf', '/etc/nsswitch.conf'):
        try:
            report['resolver'][name] = [line for line in Path(name).read_text().splitlines()
                if line.startswith(('nameserver ', 'search ', 'options ', 'hosts:'))]
        except OSError as exc:
            report['resolver'][name] = type(exc).__name__
    def inspect(host):
        # getent exercises the same NSS configuration used by ordinary host applications.
        return host, {'nss': probe(['getent', 'ahostsv4', host]),
                      'https': probe(['curl', '--head', '--silent', '--show-error',
                        '--connect-timeout', '3', '--max-time', '6', '--output', '/dev/null',
                        '--write-out', 'http=%{http_code} remote=%{remote_ip}\n', 'https://'+host+'/'])}
    with ThreadPoolExecutor(max_workers=5) as pool:
        for host, result in pool.map(inspect, HOSTS):
            report['hosts'][host] = result
    Path('build-network-diagnostics.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
