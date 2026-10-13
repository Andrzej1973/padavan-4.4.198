#!/usr/bin/env python3
"""Run the actual WR config verifier for normalized disabled SQM forms."""
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

for selector in ('CONFIG_FIRMWARE_INCLUDE_SQM=n','# CONFIG_FIRMWARE_INCLUDE_SQM is not set','',
                 'CONFIG_FIRMWARE_INCLUDE_SQM=y','CONFIG_FIRMWARE_INCLUDE_SQM=m'):
    report=File()
    arguments=argparse.Namespace(requested=File('CONFIG_FIRMWARE_INCLUDE_SQM=n'),
        effective=File('CONFIG_VENDOR=Ralink\nCONFIG_PRODUCT=MT7621\n'+selector),
        kernel=File('CONFIG_RALINK_BUILTIN_DTB_NAME="wr1200js"'),report=report)
    failed=False
    with patch.object(argparse.ArgumentParser,'parse_args',return_value=arguments):
        try:verifier.main()
        except SystemExit:failed=True
    enabled=selector.endswith('=y') or selector.endswith('=m')
    assert failed==enabled,selector
    data=json.loads(report.text)
    assert bool(data['mismatches'])==enabled
    assert data['options'][0]['requested_key']=='CONFIG_FIRMWARE_INCLUDE_SQM'
print('PASS actual WR config verifier: disabled normalized SQM accepted; enabled SQM rejected')
