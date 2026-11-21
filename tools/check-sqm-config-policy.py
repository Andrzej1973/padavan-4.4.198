#!/usr/bin/env python3
"""Exercise actual config verifier for inclusion and legacy disabled profiles."""
import argparse
import importlib.util
import json
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
for key in required:
    altered=dict(required);altered[key]='n'
    failed,data=run('y','CONFIG_FIRMWARE_INCLUDE_SQM=y',altered)
    assert failed and key in data['mismatches'],key
profile=verifier.read_config(Path(__file__).resolve().parents[1]/'configs.build/wr1200js.config')
assert profile.get('CONFIG_FIRMWARE_INCLUDE_SQM')=='y', 'WR1200JS must include CAKE/SQM; runtime default is separately OFF'
print('PASS SQM inclusion, normalized historical exclusion and missing CAKE/IFB/ingress components refused')
