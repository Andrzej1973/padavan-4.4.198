#!/usr/bin/env python3
"""Execute the actual lane selector; verify source default and explicit control."""
import os,re,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[2]
workflow=(root/'.github/workflows/build-padavan-4.4-wr1200js.yml').read_text()
parent=(root/'.github/workflows/build-multiple-boards.yml').read_text()
comparison=(root/'.github/workflows/compare-toolchain-firmware.yml').read_text()
assert re.search(r'toolchain_variant:\n(?:        .*\n)*?        default: source\n',workflow)
assert 'options: [source, pinned]' in parent
assert "toolchain_variant: ${{ inputs.toolchain_variant || 'source' }}" in parent
assert 'toolchain_variant: pinned' in comparison and 'toolchain_variant: source' in comparison
start=workflow.index('          case "$VARIANT:$SUFFIX" in');end=workflow.index('          esac',start)+len('          esac')
script='\n'.join(line[10:] for line in workflow[start:end].splitlines())
for variant,suffix,ok in [('source','',True),('pinned','',True),('source','-source',True),('pinned','-control',True),('source','-control',False),('pinned','-source',False),('unknown','',False),('source','../bad',False),('','',False)]:
 result=subprocess.run(['bash','-euc',script],env={**os.environ,'VARIANT':variant,'SUFFIX':suffix},capture_output=True,text=True)
 assert (result.returncode==0)==ok,(variant,suffix,result.stderr)
# Firmware source override must not load missing/new compiler helpers from an
# older source checkout. Verification tools are pinned separately to dispatch.
assert 'path: .toolchain-verification' in workflow and 'ref: ${{ github.sha }}' in workflow
for script in ['check-owned-candidate.py','fetch-owned-candidate.py','check-extraction.py','install-candidate.py']:
 assert 'python3 .toolchain-verification/tools/toolchain/'+script in workflow
print('PASS actual compiler lane cases, source development default, explicit pinned control and separate historical-source loader')
