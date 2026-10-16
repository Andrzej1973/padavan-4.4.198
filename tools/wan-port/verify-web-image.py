#!/usr/bin/env python3
"""Check shipped WAN controls and labels; never claim runtime verification."""
import argparse
import hashlib
import json
from pathlib import Path


def verify(www):
    page_path = www / 'Advanced_WAN_Content.asp'
    page = page_path.read_text(encoding='utf-8')
    checks = {}
    for marker in ['var wr_wan_socket_supported', 'wr_selected',
                   'showhide_div("wan_src_phy", 1)', 'WAN_Socket_Confirm',
                   'WAN_Socket_Help', 'id="wr_wan_socket_help"']:
        checks['page:' + marker] = marker in page
    hashes = {page_path.name: hashlib.sha256(page_path.read_bytes()).hexdigest()}
    for language in ['EN', 'UK', 'RU']:
        path = www / (language + '.dict')
        lines = path.read_text(encoding='utf-8').splitlines()
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        for key in ['WAN_Socket_Confirm', 'WAN_Socket_Help']:
            values = [line.split('=', 1)[1] for line in lines if line.startswith(key + '=')]
            checks[language + ':' + key] = len(values) == 1 and bool(values[0].strip())
            if key.endswith('Confirm') and values:
                # The template inserts this text in a single-quoted JS literal.
                checks[language + ':safe-confirm-literal'] = not any(c in values[0] for c in "'\\\r\n")
    return {'schema': 1, 'runtime_verified': False, 'checks': checks,
            'sha256': hashes, 'success': all(checks.values())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('www', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.www)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(('PASS' if report['success'] else 'FAIL') + ' WAN WebUI image checks')
    raise SystemExit(0 if report['success'] else 1)
