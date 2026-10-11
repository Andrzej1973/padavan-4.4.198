#!/usr/bin/env python3
"""Stage exactly one firmware and its central requested configuration."""
import os
from pathlib import Path
import shutil
import sys

artifact = Path(sys.argv[1])
output = Path(sys.argv[2])
board = sys.argv[3]
if not board.replace('-', '').isalnum():
    raise SystemExit('Invalid board ID')
images = list(artifact.rglob('*.trx'))
configs = list(artifact.rglob('firmware-requested.config'))
guides = list(artifact.rglob('SETUP_*.txt'))
if len(images) != 1 or len(configs) != 1 or len(guides) != 1:
    raise SystemExit('Require exactly one TRX, requested config and setup guide')
if output.exists():
    raise SystemExit('Output must be a fresh directory')
output.mkdir(parents=True)
shutil.copyfile(images[0], output / images[0].name)
shutil.copyfile(configs[0], output / (board + '.config'))
shutil.copyfile(guides[0], output / guides[0].name)
with open(os.environ['GITHUB_OUTPUT'], 'a') as result:
    result.write('archive_name=' + images[0].stem + '_TEST\n')
print('Staged firmware, configuration and model setup guide')
