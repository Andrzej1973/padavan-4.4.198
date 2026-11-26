#!/usr/bin/env python3
"""Exercise actual config verifier for inclusion and legacy disabled profiles."""
import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('wr_config',Path(__file__).with_name('verify-wr1200js-config.py'))
verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
class File:
    def __init__(self,text=''):self.text=text
    def read_text(self,**kwargs):return self.text
    def write_text(self,text,**kwargs):self.text=text

required={'CONFIG_NET_SCH_CAKE':'m','CONFIG_IFB':'m','CONFIG_NET_SCHED':'y',
          'CONFIG_NET_CLS_ACT':'y','CONFIG_NET_SCH_INGRESS':'m',
          'CONFIG_NET_CLS_U32':'m','CONFIG_NET_ACT_MIRRED':'m'}
def run(requested,selector,kernel_values):
    report=File()
    kernel='CONFIG_RALINK_BUILTIN_DTB_NAME="wr1200js"\nCONFIG_HW_NAT=y\nCONFIG_RA_NAT_NONE=y\n'
    kernel+='\n'.join(k+'='+v for k,v in kernel_values.items())
    arguments=argparse.Namespace(requested=File('CONFIG_FIRMWARE_INCLUDE_SQM='+requested),
        effective=File('CONFIG_VENDOR=Ralink\nCONFIG_PRODUCT=MT7621\n'+selector),
        kernel=File(kernel),report=report)
    failed=False
    with patch.object(argparse.ArgumentParser,'parse_args',return_value=arguments):
        try:verifier.main()
        except SystemExit:failed=True
    return failed,json.loads(report.text)
for requested in ('n','y'):
    for selector in ('CONFIG_FIRMWARE_INCLUDE_SQM=n','# CONFIG_FIRMWARE_INCLUDE_SQM is not set','',
                     'CONFIG_FIRMWARE_INCLUDE_SQM=y','CONFIG_FIRMWARE_INCLUDE_SQM=m'):
        failed,data=run(requested,selector,required)
        valid=selector.endswith('=y') if requested=='y' else not selector.endswith(('=y','=m'))
        assert failed != valid,(requested,selector,data)
        assert data['mismatches']==([] if valid else ['CONFIG_FIRMWARE_INCLUDE_SQM'])
failed,data=run('n','CONFIG_FIRMWARE_INCLUDE_SQM=n',
                {'CONFIG_DEVMEM':'y','CONFIG_MODULE_SIG':'n'})
assert not failed
security=data['kernel_security_config']
assert security['CONFIG_DEVMEM']=='y'
assert security['CONFIG_MODULE_SIG']=='n'
assert security['CONFIG_SECCOMP'] is None
for key in required:
    altered=dict(required);altered[key]='n'
    failed,data=run('y','CONFIG_FIRMWARE_INCLUDE_SQM=y',altered)
    assert failed and key in data['mismatches'],key
repo=Path(__file__).resolve().parents[1]
profile=verifier.read_config(repo/'configs.build/wr1200js.config')
assert profile.get('CONFIG_FIRMWARE_INCLUDE_SQM')=='n', 'standard WR1200JS profile must exclude CAKE/SQM'
workflow=(repo/'.github/workflows/build-padavan-4.4-wr1200js.yml').read_text()
assert "profile)\n              sed -i 's/^CONFIG_FIRMWARE_INCLUDE_SQM=[yn]$/CONFIG_FIRMWARE_INCLUDE_SQM=y/'" in workflow
assert "excluded)\n              sed -i 's/^CONFIG_FIRMWARE_INCLUDE_SQM=[yn]$/CONFIG_FIRMWARE_INCLUDE_SQM=n/'" in workflow
print('PASS standard SQM exclusion, explicit candidate inclusion, normalized effective config and missing CAKE/IFB/ingress components refused')


def check_dashboard(selector):
    tools=Path(__file__).with_name('hybrid-dashboard')
    with tempfile.TemporaryDirectory(prefix='wr-sqm-dashboard-') as directory:
        source=Path(directory)
        www=source/'trunk/user/www'
        classic=www/'n56u_ribbon_fixed'
        classic.mkdir(parents=True)
        (www/'Makefile').write_text('WEBUI_NAME=n56u_ribbon_fixed\nromfs:\n\tcp -R $(WEBUI_NAME) $(ROMFS_DIR)/www\n')
        (source/'trunk/.config').write_text(selector+'\n')
        enabled=selector.endswith('=y')
        routes=('index.asp','system_status_data.asp','status_wanlink.asp','status_lanlink.asp',
                'device-map/internet.asp','device-map/intranet.asp','device-map/clients.asp',
                'Main_WStatus2g_Content.asp','Advanced_Wireless_Content.asp','Main_LogStatus_Content.asp')
        for route in routes+(('Advanced_SQM.asp',) if enabled else ()):
            path=classic/route
            path.parent.mkdir(parents=True,exist_ok=True)
            path.touch()
        command=[sys.executable,str(tools/'prepare.py'),str(source)]
        subprocess.run(command+([] if enabled else ['--without-sqm']),check=True)
        romfs=source/'trunk/romfs'
        romfs.mkdir()
        subprocess.run(['make','-s','-C',str(www),'romfs','ROMFS_DIR='+str(romfs)],check=True)
        check=[sys.executable,str(tools/'check-image.py'),str(source)]
        subprocess.run(check,check=True)
        index=romfs/'www/hybrid/index.html'
        assert ('/Advanced_SQM.asp' in index.read_text())==enabled
        if enabled:
            (romfs/'www/Advanced_SQM.asp').unlink()
            expected='Missing Classic route: Advanced_SQM.asp'
        else:
            shutil.copyfile(tools/'index.html',index)
            expected='Missing or altered hybrid asset: index.html'
        refused=subprocess.run(check,capture_output=True,text=True)
        assert refused.returncode==1 and expected in refused.stderr

for selector in ('CONFIG_FIRMWARE_INCLUDE_SQM=y','CONFIG_FIRMWARE_INCLUDE_SQM=n',
                 '# CONFIG_FIRMWARE_INCLUDE_SQM is not set'):
    check_dashboard(selector)
print('PASS SQM-dependent Hybrid navigation and ROMFS gate with actual copy recipe')
