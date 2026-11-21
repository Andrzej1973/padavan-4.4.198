#!/usr/bin/env python3
"""Exercise reviewed v25b LF/CRLF pins and reject a changed source payload."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path, help='Generated later/v25b input')
    args = parser.parse_args()
    source = args.candidate.resolve(strict=True)
    preparer = Path(__file__).with_name('prepare-v25b-generation-bound.py')
    with tempfile.TemporaryDirectory(prefix='wr-iot-v25b-eol-') as directory:
        root = Path(directory).resolve()
        for mode in ('LF', 'CRLF', 'corrupt'):
            case = root / mode
            shutil.copytree(source, case)
            path = case / 'tx_rx/txs.c'
            data = path.read_bytes().replace(b'\r\n', b'\n')
            if mode == 'CRLF':
                data = data.replace(b'\n', b'\r\n')
            if mode == 'corrupt':
                data += b'\n/* unexpected source change */\n'
            path.write_bytes(data)
            output = root / (mode + '-output')
            result = subprocess.run(
                [sys.executable, str(preparer), str(case), str(output)],
                capture_output=True, text=True, timeout=30,
            )
            if mode == 'corrupt':
                if (not result.returncode or output.exists() or
                        'Unreviewed v25b TxS source' not in result.stderr):
                    raise SystemExit('Changed source was not rejected before output')
            elif result.returncode or (output / 'tx_rx/txs.c').read_bytes() != data:
                raise SystemExit(mode + ' candidate failed: ' + result.stderr)
            print('PASS generation source pin: ' + mode)


if __name__ == '__main__':
    main()
