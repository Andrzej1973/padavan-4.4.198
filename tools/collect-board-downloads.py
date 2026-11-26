#!/usr/bin/env python3
"""Aggregate per-board artifacts without claiming failed/missing builds passed."""
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

selected = json.loads(Path('selection/selected-boards.json').read_text())
revision = os.environ.get('SOURCE_SHA', '')
if not re.fullmatch(r'[0-9a-f]{40}', revision):
    raise SystemExit('Missing or invalid selected source revision')
out = Path('downloads')
out.mkdir(exist_ok=True)
records = []
lines = ['# Padavan 4.4.198 firmware downloads', '',
         'Device runtime verification remains separate from build verification.', '']
for board in selected:
    board_id = board['id']
    if not board_id.replace('-', '').isalnum():
        raise SystemExit('Invalid board ID')
    artifact = Path('board-artifacts') / ('padavan-linux-4.4.198-' + board_id)
    status_file = Path('board-status') / ('board-build-status-' + board_id) / 'board-build-status.json'
    # download-artifact extracts a single matched artifact directly into path.
    # This fallback is only unambiguous when exactly one board was selected.
    if len(selected) == 1:
        if not artifact.exists():
            artifact = Path('board-artifacts')
        if not status_file.is_file():
            status_file = Path('board-status/board-build-status.json')
    status_record = json.loads(status_file.read_text()) if status_file.is_file() else None
    if status_record and status_record.get('board') != board_id:
        raise SystemExit('Status artifact belongs to a different board')
    status = status_record['status'] if status_record else 'missing-status'
    target = out / board_id
    images = list(artifact.rglob('*.trx')) if artifact.exists() else []
    record = {'board': board_id, 'build_status': status, 'images': []}
    if status == 'success':
        if len(images) != 1:
            raise SystemExit('Successful build must supply exactly one TRX: ' + board_id)
        source = images[0]
        if status_record.get('revision') != revision or not source.name.endswith('_' + revision[:8] + '.trx'):
            raise SystemExit('TRX revision differs from selected source: ' + board_id)
        relative = source.relative_to(artifact)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        report = json.loads((artifact / 'firmware-image-checks.json').read_text())
        if report.get('sha256') != digest or status_record.get('sha256') != digest:
            raise SystemExit('TRX checksum differs from build evidence: ' + board_id)
        if board_id == 'wr1200js':
            contents = json.loads((artifact / 'final-content-check.json').read_text())
            if contents.get('image_sha256') != digest:
                raise SystemExit('TRX checksum differs from final ROMFS evidence: ' + board_id)
            sqm_profile = os.environ.get('SQM_PROFILE', 'excluded')
            if sqm_profile not in ('excluded', 'profile'):
                raise SystemExit('Invalid requested SQM profile')
            if contents.get('sqm_excluded_verified') is not (sqm_profile == 'excluded'):
                raise SystemExit('ROMFS evidence differs from requested SQM profile')
            provenance = json.loads((artifact / 'wr1200js-build-inputs.json').read_text())
            if (provenance.get('source_sha') != revision or provenance.get('image_sha256') != digest
                    or provenance.get('sqm_profile') != sqm_profile):
                raise SystemExit('WR1200JS build inputs refer to a different revision, TRX or SQM profile')
            toolchain = os.environ.get('TOOLCHAIN_VARIANT', 'source')
            if provenance.get('toolchain_variant') != toolchain:
                raise SystemExit('WR1200JS build inputs refer to a different toolchain variant')
            record['toolchain_variant'] = toolchain
            host = os.environ.get('BUILD_HOST', 'ubuntu-24.04')
            if provenance.get('build_host', {}).get('requested') != host:
                raise SystemExit('WR1200JS build inputs refer to a different build host')
            record['build_host'] = host
            for name in ('firmware-requested.config', 'firmware-effective.config', 'kernel-effective.config'):
                config_digest = hashlib.sha256((artifact / name).read_bytes()).hexdigest()
                if provenance['input_sha256'].get(name) != config_digest:
                    raise SystemExit('WR1200JS configuration differs from build inputs: ' + name)
            if sqm_profile == 'profile':
                if contents.get('sqm_included_verified') is not True:
                    raise SystemExit('Missing final TRX evidence for included SQM files')
                cake_report = json.loads((artifact / 'cake-image-checks.json').read_text())
                if cake_report.get('image_sha256') != digest:
                    raise SystemExit('TRX checksum differs from CAKE verification report')
                checks = cake_report.get('checks', {})
                required = ('profile_included', 'kernel_components', 'factory_off', 'not_default_qdisc')
                report_board = cake_report.get('board')
                if (not isinstance(report_board, str) or report_board.lower() != board_id
                        or not isinstance(checks, dict)
                        or any(checks.get(key) is not True for key in required)
                        or any(value is not True for value in checks.values())):
                    raise SystemExit('CAKE inclusion or default-OFF verification failed')
            record['sqm_profile'] = 'without-cake' if sqm_profile == 'excluded' else 'with-cake'
        shutil.copytree(str(artifact), str(target))
        (target / 'SHA256SUMS').write_text(digest + '  ' + relative.as_posix() + '\n')
        record['images'].append({'file': (Path(board_id) / relative).as_posix(),
                                 'sha256': digest, 'bytes': source.stat().st_size})
        lines.append('- {}: {} — [{}]({})'.format(board['name'], status,
                     source.name, record['images'][0]['file']))
    else:
        record['image_status'] = 'build-not-confirmed'
        lines.append('- {}: {} — firmware withheld.'.format(board['name'], status))
    records.append(record)
result = {'workflow_build_result': os.environ.get('BUILD_RESULT', 'unknown'),
          'source_revision': revision, 'boards': records}
result['all_selected_images_built'] = bool(records) and all(
    record['build_status'] == 'success' and len(record['images']) == 1
    for record in records)
(out / 'index.json').write_text(json.dumps(result, indent=2) + '\n')
(out / 'README.md').write_text('\n'.join(lines) + '\n')
with open(os.environ.get('GITHUB_STEP_SUMMARY', os.devnull), 'a') as summary:
    summary.write('\n'.join(lines) + '\n')
print(json.dumps(result))
