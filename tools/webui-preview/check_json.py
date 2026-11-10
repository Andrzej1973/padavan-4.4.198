#!/usr/bin/env python3
"""Run actual Modern C JSON handler with system/NVRAM fixtures; host-only evidence."""
import json
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-modern-json-semantics-') as scratch:
    binary = str(Path(scratch) / 'check')
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-I' + str(HERE), str(HERE / 'check-wr-modern-json.c'),
                    '-o', binary], check=True)
    for case in range(4):
        data = json.loads(subprocess.check_output([binary, str(case)]))
        assert data['memoryPercent'] == (50 if case == 0 else None)
        assert data['pages']['monitoring']['fields'][0]['value'] == ('50%' if case == 0 else 'Н/Д')
        assert data['internet']['status'] == 'IP задано · доступ не перевірено'
    ssid = 'IoT " \\ \b\f\n\r\t\x01 <script> тест'
    data = json.loads(subprocess.check_output([binary, '0', ssid]))
    assert data['wifi'][0]['ssid'] == ssid
    assert all('psk' not in key.lower() and 'password' not in key.lower() for key in data)
print('PASS actual C JSON handler: normal/error/zero/inconsistent RAM; WAN address is not reachability; ASan/UBSan; scratch removed')
