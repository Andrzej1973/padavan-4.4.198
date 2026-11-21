#!/usr/bin/env python3
"""Compose the reviewed main-open claim into an isolated queue bundle only."""
import argparse
import ast
import hashlib
import json
import runpy
import shutil
from pathlib import Path

here = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('queue', type=Path)
p.add_argument('reviewed_open', type=Path, nargs='?', help='Optional historical comparison input')
p.add_argument('output', type=Path)
a = p.parse_args()
queue, output = a.queue.resolve(), a.output.resolve()
reviewed = a.reviewed_open.resolve() if a.reviewed_open else None
if output.exists() or output == queue or output == reviewed or output in queue.parents or (reviewed is not None and output in reviewed.parents):
    p.error('output must be a new separate directory')
manifest = json.loads((queue.parent / 'manifest.json').read_text(encoding='utf-8'))
if not (manifest.get('complete_driver_tree') is False and
        manifest.get('production_installed') is False and
        manifest.get('virtual_open_claim_composed') is False and
        manifest.get('main_open_owner_composed') is False):
    p.error('queue manifest is not the reviewed partial input')
if manifest.get('source_revision') != 'c25283e915a2a00a763774dd255b14aff997285e':
    p.error('queue source revision changed')
for record in manifest['files']:
    path = queue / record['path']
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
        p.error('queue input differs from manifest: ' + record['path'])
reviewed_hashes = {
    'common/cmm_cfg.c': '5d0eb4c4057dd485d9c15d1bfdea69a6744ffb3461c0624590b191904d7ea388',
    'include/rt_os_net.h': 'bc362d748229d88e8482547139956f2fa80727e9aa87903d30904396c1e43471',
}
if reviewed is not None:
    for name, expected in reviewed_hashes.items():
        if hashlib.sha256((reviewed / name).read_bytes()).hexdigest() != expected:
            p.error('reviewed open source changed: ' + name)

main_fragments = runpy.run_path(str(here / 'prepare-main-open-owner-candidate.py'))
main_open = main_fragments['MAIN_OPEN']
tree = ast.parse((here / 'prepare-virtual-open-claim-candidate.py').read_text(encoding='utf-8'))
def literal(name):
    values = [ast.literal_eval(n.value) for n in ast.walk(tree)
              if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name
                                                  for t in n.targets)]
    if len(values) != 1:
        raise ValueError('ambiguous reviewed fragment: ' + name)
    return values[0].decode('utf-8')
generated_header = literal('claimed')
generated_dispatch = literal('checked')
marker = 'valid = VIRTUAL_IF_NUM(pAd) > 0 &&'
if generated_dispatch.count(marker) != 1:
    raise ValueError('reviewed auxiliary dispatcher anchor changed')
generated_dispatch = generated_dispatch.replace(marker, main_fragments['MAIN_DISPATCH'] + marker, 1)

def function(text, signature):
    if text.count(signature) != 1:
        raise ValueError('ambiguous function: ' + signature)
    start = text.index(signature)
    opening = text.index('{', start)
    depth, end = 1, opening + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]

def replace_one(text, old, new, label):
    if text.count(old) != 1:
        raise ValueError(f'{label}: expected one anchor, found {text.count(old)}')
    return text.replace(old, new, 1)

def source(name):
    return (queue / name).read_text(encoding='utf-8')

changes = {}
name = 'include/rtmp_cmd.h'
changes[name] = replace_one(source(name),
    '\tIN\tint (*rt28xx_close)(VOID *net_dev);',
    '\tIN\tint (*rt28xx_close)(VOID *net_dev);\n'
    '\tIN\tVOID *if_dev;\n'
    '\tIN\tunsigned long owner_generation, owner_serial, owner_epoch;\n'
    '\tIN\tint owner_operation;', name)

name = 'include/rt_os_net.h'
header = source(name)
header = replace_one(header, '#include "chip/chip_id.h"',
                     '#include "chip/chip_id.h"\n#include "radio-transition.h"', name)
old_init = '{ rt28xx_open, rt28xx_close };'
if header.count(old_init) != 2:
    raise ValueError('legacy UP/DOWN initializers changed')
header = header.replace(old_init, '{ rt28xx_open, rt28xx_close, NULL, 0, 0, 0, 0 };')
reviewed_header = ((reviewed / name).read_text(encoding='utf-8') if reviewed else generated_header)
claimed = function(reviewed_header, '__inline INT VIRTUAL_IF_UP_CLAIM(')
header = replace_one(header, '__inline VOID VIRTUAL_IF_DOWN(VOID *pAd)',
                     claimed + '\n\n__inline VOID VIRTUAL_IF_DOWN(VOID *pAd)', name)
changes[name] = header

name = 'include/rtmp.h'
changes[name] = replace_one(source(name),
    '\twait_queue_head_t wr_iot_registration_wait;',
    '\twait_queue_head_t wr_iot_registration_wait;\n'
    '\twait_queue_head_t wr_iot_ticket_wait;', name)
name = 'common/rtmp_init.c'
changes[name] = replace_one(source(name),
    'init_waitqueue_head(&pAd->wr_iot_registration_wait);',
    'init_waitqueue_head(&pAd->wr_iot_registration_wait);\n'
    '\t\tinit_waitqueue_head(&pAd->wr_iot_ticket_wait);', name)

name = 'common/cmm_cfg.c'
dispatch = source(name)
reviewed_dispatch = ((reviewed / name).read_text(encoding='utf-8') if reviewed else generated_dispatch)
start = reviewed_dispatch.index('\n\t\t\tif (pInfConf->owner_generation')
end = reviewed_dispatch.index('\n\t\t\t/* Arithmetic guard only;', start)
claim_block = reviewed_dispatch[start:end]
anchor = ('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_UP:\n'
          '\t\t/* interface up */\n\t\t{\n'
          '\t\t\tRT_CMD_INF_UP_DOWN *pInfConf = (RT_CMD_INF_UP_DOWN *)pData;')
dispatch = replace_one(dispatch, '#include "rt_config.h"',
                       '#include "rt_config.h"\n#include "virtual-open-claim.h"', name)
changes[name] = replace_one(dispatch, anchor, anchor + claim_block, name)

name = 'os/linux/rt_main_dev.c'
main = source(name)
old_main = function(main, 'int MainVirtualIF_open(struct net_device *net_dev)')
if 'if (VIRTUAL_IF_UP(pAd) != 0)' not in old_main:
    raise ValueError('queue main-open baseline changed')
main = replace_one(main, old_main, main_open, name)
main = replace_one(main, 'static void wr_iot_hold_netdev(const void *device)',
    '#include "wr-iot-radio-ticket-wait.inc"\n'
    'static void wr_iot_hold_netdev(const void *device)', name)
changes[name] = main

for name, data in changes.items():
    if 'wr_iot_main_recovery' in source(name) and 'wr_iot_main_recovery' not in data:
        raise ValueError('recovery storage lost in ' + name)
if 'VIRTUAL_IF_UP_CLAIM(pAd, net_dev, &ticket, generation)' not in changes['os/linux/rt_main_dev.c']:
    raise ValueError('main-open ticket was not passed')

shutil.copytree(queue, output)
for name, data in changes.items():
    (output / name).write_text(data, encoding='utf-8', newline='\n')
shutil.copyfile(here / 'radio-ticket-wait.inc',
                output / 'include/wr-iot-radio-ticket-wait.inc')
records = manifest['files']
for record in records:
    if record['path'] in changes:
        record['stage'] += '+main-open-claim'
        record['sha256'] = hashlib.sha256((output / record['path']).read_bytes()).hexdigest()
records.append({'path': 'include/wr-iot-radio-ticket-wait.inc',
                'stage': 'main-open-claim', 'purpose': 'driver',
                'sha256': hashlib.sha256((output / 'include/wr-iot-radio-ticket-wait.inc').read_bytes()).hexdigest()})
manifest['main_open_claim_composed'] = True
manifest['virtual_open_claim_composed'] = False  # Other families still use the legacy ABI.
manifest['main_open_owner_composed'] = False  # No deferred checked-close worker.
manifest['failed_main_open_pin_retention_proven'] = False
manifest['complete_driver_tree'] = False
manifest['production_installed'] = False
(output.parent / (output.name + '-composition.json')).write_text(
    json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print('PASS isolated main-open claim composition; other families and recovery remain unbound')
