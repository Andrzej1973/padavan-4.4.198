#!/usr/bin/env python3
"""Compose a separate source-only ra2 beacon experiment from a verified candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
source = args.source.resolve()
output = args.output.resolve()
if output.exists() or source == output or source in output.parents or output in source.parents:
    parser.error('A new separate output directory is required')
manifest_path = Path(str(source) + '.manifest.json')
manifest_bytes = manifest_path.read_bytes()
manifest = json.loads(manifest_bytes)
if manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False:
    parser.error('Expected a source-only isolated candidate')
actual = {str(path.relative_to(source)): hashlib.sha256(path.read_bytes()).hexdigest()
          for path in source.rglob('*') if path.is_file()}
if actual != manifest.get('merged_driver_sha256'):
    parser.error('Candidate source differs from its manifest')
if 'linux_open_api' not in manifest:
    parser.error('Expected final Linux API candidate')
here = Path(__file__).resolve().parent
policy = runpy.run_path(str(here / 'ra2-beacon-no-host-status.py'))
lower = runpy.run_path(str(here / 'ra2-beacon-no-host-submit.py'))
# The static no-host policy relies on the MT helper's zero PID and exact BSS
# metadata from its first invocation. Reject drift before writing any output.
connect_input = (source / 'ap/ap_connect.c').read_text()
constructor_start = connect_input.index('UINT32 write_tmac_info_beacon(')
constructor_end = connect_input.index('\n}', constructor_start) + 2
constructor = connect_input[constructor_start:constructor_end]
required_metadata = (
    'NdisZeroMemory((UCHAR *)&mac_info, sizeof(mac_info));',
    'mac_info.q_idx = Q_IDX_BCN;',
    'mac_info.TxSPriv = apidx;',
    'mac_info.bss_idx = apidx;',
    'write_tmac_info(pAd, tmac_buf, &mac_info, BeaconTransmit);',
)
if any(constructor.count(item) != 1 for item in required_metadata) or 'mac_info.PID' in constructor:
    parser.error('MT beacon helper identity or zero-PID contract changed')
changes = {}
changes['mac/mt_mac.c'] = policy['compose']((source / 'mac/mt_mac.c').read_text())
changes['tx_rx/txs.c'] = policy['compose_callback']((source / 'tx_rx/txs.c').read_text())
changes['ap/ap_connect.c'], changes['include/rtmp.h'] = policy['compose_builder_ticket'](
    (source / 'ap/ap_connect.c').read_text(), (source / 'include/rtmp.h').read_text())
changes['include/wr-iot-beacon-producer-kernel.h'] = policy['compose_periodic'](
    (source / 'include/wr-iot-beacon-producer-kernel.h').read_text())
changes['common/cmm_mac_pci.c'] = lower['compose']((source / 'common/cmm_mac_pci.c').read_text())
for name in ('ra2-beacon-dma-window.h', 'ra2-beacon-no-host-txd.h', 'ra2-beacon-no-host-packet.h'):
    changes['include/' + name] = (here / name).read_text()
for name in changes:
    changes[name] = changes[name].replace('#include "beacon-producer-gate.h"',
                                        '#include "wr-iot-beacon-producer-gate.h"')
if not (source / 'include/wr-iot-beacon-producer-gate.h').is_file():
    parser.error('Missing prepared SDK producer-gate header')
# Validate every transformation before creating the output tree.
shutil.copytree(source, output)
for name, content in changes.items():
    (output / name).write_text(content)
hashes = {str(path.relative_to(output)): hashlib.sha256(path.read_bytes()).hexdigest()
          for path in output.rglob('*') if path.is_file()}
manifest['merged_driver_sha256'] = hashes
manifest['candidate_driver_sha256'] = hashes
manifest['ra2_no_host_experiment'] = {
    'input_manifest_sha256': hashlib.sha256(manifest_bytes).hexdigest(),
    'production_installed': False,
    'target_compiled': False,
    'runtime_verified': False,
    'activation_ready': False,
    'remaining': ['cold epoch and shared PID handling', 'owner release/reopen',
                  'full target compilation and physical verification'],
    'changed_paths': sorted(changes),
}
Path(str(output) + '.manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Prepared separate ra2 source experiment with nine composed paths')
