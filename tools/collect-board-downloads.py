#!/usr/bin/env python3
"""Aggregate per-board artifacts without claiming failed/missing builds passed."""
import hashlib
import json
import os
import shutil
from pathlib import Path

selected = json.loads(Path('selection/selected-boards.json').read_text())
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
    status = json.loads(status_file.read_text())['status'] if status_file.is_file() else 'missing-status'
    target = out / board_id
    images = list(artifact.rglob('*.trx')) if artifact.exists() else []
    record = {'board': board_id, 'build_status': status, 'images': []}
    if len(images) == 1:
        shutil.copytree(str(artifact), str(target))
        source = images[0]
        relative = source.relative_to(artifact)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        (target / 'SHA256SUMS').write_text(digest + '  ' + relative.as_posix() + '\n')
        record['images'].append({'file': (Path(board_id) / relative).as_posix(),
                                 'sha256': digest, 'bytes': source.stat().st_size})
        lines.append('- {}: {} — [{}]({})'.format(board['name'], status,
                     source.name, record['images'][0]['file']))
    else:
        record['image_status'] = 'missing-or-ambiguous'
        lines.append('- {}: {} — no unique firmware image.'.format(board['name'], status))
    records.append(record)
result = {'workflow_build_result': os.environ.get('BUILD_RESULT', 'unknown'), 'boards': records}
result['all_selected_images_built'] = bool(records) and all(
    record['build_status'] == 'success' and len(record['images']) == 1
    for record in records)
(out / 'index.json').write_text(json.dumps(result, indent=2) + '\n')
(out / 'README.md').write_text('\n'.join(lines) + '\n')
with open(os.environ.get('GITHUB_STEP_SUMMARY', os.devnull), 'a') as summary:
    summary.write('\n'.join(lines) + '\n')
print(json.dumps(result))
