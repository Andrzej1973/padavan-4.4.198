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
    config=data['wifiConfiguration']
    assert config['schemaVersion']==1 and config['source']=='stored-nvram'
    assert config['runtimeVerified'] is False and config['shared']=='0'
    assert set(config['bands'])=={'24','5'}
    public={'ssid','auth_mode','wep_x','wpa_mode','crypto','radio_x','closed','channel','HT_BW','gmode','HT_EXTCHA'}
    for band in config['bands'].values():
        assert set(band)==public
        assert all(isinstance(value,str) for value in band.values())
    guest_fields={'enable','ssid','closed','auth_mode','wpa_mode','crypto','lan_isolate','ap_isolate','macrule','mcs_mode','date_x','time_x','time2_x'}
    assert set(config['guests'])=={'24','5'}
    for guest in config['guests'].values():
        assert set(guest)==guest_fields
        assert all(isinstance(value,str) for value in guest.values())
    assert config['guests']['24']['ssid']=='Guest-24'
    assert config['guests']['5']['ssid']=='Guest-5'
    assert config['guests']['24']['date_x']=='0111110'
    assert config['bands']['24']['ssid']==ssid
    assert config['bands']['5']['ssid']=='Home-5G'
    assert config['bands']['24']['channel']=='6'
    assert config['bands']['5']['channel']=='44'

    assert all('psk' not in key.lower() and 'password' not in key.lower() for key in data)
    empty=json.loads(subprocess.check_output([binary,'0','']))
    assert empty['wifiConfiguration']['bands']['24']['ssid']==''
    assert empty['wifi'][0]['ssid']=='N/A'  # Overview retains explicit unknown label.
    for fixture in ('password-intent','password-request','radio24-validate','guest-schedule','guest-request','guest-adapter','guest-transport'):
        password_binary=str(Path(scratch)/fixture)
        subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror',
                        '-fsanitize=address,undefined','-fno-pie','-no-pie',
                        '-I'+str(HERE.parent/'shared-wifi'),'-I'+str(HERE),
                        str(HERE/('check-'+fixture+'.c')),'-o',password_binary],check=True)
        subprocess.run([password_binary],check=True)
print('PASS actual C JSON handler: normal/error/zero/inconsistent RAM; WAN address is not reachability; ASan/UBSan; scratch removed')
