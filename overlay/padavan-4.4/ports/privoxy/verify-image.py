#!/usr/bin/env python3
"""Verify Privoxy packaging; target runtime remains unverified."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('trunk', type=Path)
parser.add_argument('report', type=Path)
args = parser.parse_args()
root = args.trunk.resolve() / 'romfs'
checks = {}
details = {}

def target(name):
    parts = list(Path(name.lstrip('/')).parts)
    current = root
    hops = 0
    while parts:
        part = parts.pop(0)
        current = current.parent if part == '..' else current / part
        if current != root and root not in current.parents:
            raise RuntimeError('ROMFS path escaped root')
        if current.is_symlink():
            hops += 1
            if hops > 40:
                raise RuntimeError('ROMFS symlink loop')
            link = os.readlink(current)
            current = root if link.startswith('/') else current.parent
            parts = list(Path(link.lstrip('/')).parts) + parts
    return current

try:
    checks['selector'] = 'CONFIG_FIRMWARE_INCLUDE_PRIVOXY=y' in (args.trunk / '.config').read_text().splitlines()
    binary = target('/usr/sbin/privoxy')
    data = binary.read_bytes()
    checks['mips_elf'] = len(data) >= 20 and data[:4] == b'\x7fELF' and data[5] == 1 and int.from_bytes(data[18:20], 'little') == 8
    checks['executable'] = bool(binary.stat().st_mode & 0o111)
    helper_path = target('/usr/bin/privoxy.sh')
    helper = helper_path.read_text()
    checks['helper'] = bool(helper_path.stat().st_mode & 0o111) and 'flock -x -n 9' in helper and '9>&-' in helper and '--config-test' in helper
    names = ['config', 'default.filter', 'user.filter', 'default.action', 'match-all.action', 'user.action', 'user.trust']
    checks['seed_configs'] = all(target('/usr/share/privoxy/privoxy/' + name).is_file() for name in names)
    checks['templates'] = target('/usr/share/privoxy/templates').is_dir()
    page = target('/www/Advanced_Services_Privoxy.asp').read_text()
    checks['observation_expiry_ui'] = all(marker in page for marker in (
        'var wrPrivoxyGeneration = 0', 'generation === wrPrivoxyGeneration',
        '}, 45000)', "document.addEventListener('visibilitychange'",
        'Date.now() - wrPrivoxySampledAt >= 45000', 'Math.floor(state) === state'))
    checks['webui'] = 'found_app_privoxy()' in page and 'login_safe()' in page and all('privoxy.' + name in page for name in ['config', 'user.action', 'user.filter', 'user.trust'])
    source_page = (args.trunk / 'user/www/n56u_ribbon_fixed/Advanced_Services_Privoxy.asp').read_text()
    checks['services_menu_index'] = 'show_menu(5,7,2)' in source_page
    status_markers = ('wr_privoxy_process_status', 'wrPrivoxyRefresh',
                      "output:'wr_privoxy_process_state'", 'document.hidden',
                      'window.setInterval(wrPrivoxyRefresh, 30000)',
                      '<% wr_privoxy_process_state(); %>',
                      'wr_privoxy_observed_at', 'toLocaleTimeString()')
    checks['runtime_status_ui'] = all(marker in source_page for marker in status_markers)
    status_keys = ('WRPrivoxyObservedTitle', 'WRPrivoxyOff', 'WRPrivoxyPresent',
                   'WRPrivoxyMissing', 'WRPrivoxyUnknown', 'WRPrivoxyStillPresent',
                   'WRPrivoxyRefresh', 'WRPrivoxyLastObservation',
                   'WRPrivoxyNoObservation', 'WRPrivoxyObservedNote')
    for locale, dictionary in (('EN', 'EN.footer'), ('UK', 'UK.dict'), ('RU', 'RU.dict')):
        translated = (args.trunk / 'user/www/dict' / dictionary).read_text(encoding='utf-8')
        checks['runtime_status_locale_' + locale.lower()] = all(
            ('\n' + key + '=') in translated for key in status_keys)
    localized_keys = set(re.findall(r'<#(Service_Privoxy_[^#]+)#>', source_page))
    for locale, dictionary in (('EN', 'EN.footer'), ('UK', 'UK.dict'), ('RU', 'RU.dict')):
        text = (args.trunk / 'user/www/dict' / dictionary).read_text(encoding='utf-8')
        available = {line.split('=', 1)[0] for line in text.splitlines() if '=' in line}
        checks['locale_' + locale.lower()] = localized_keys <= available
    httpd = target('/usr/sbin/httpd').read_bytes()
    rc = target('/sbin/rc').read_bytes()
    checks['runtime_status_backend'] = b'wr_privoxy_process_state' in httpd
    checks['httpd'] = b'found_app_privoxy' in httpd and b'privoxy.user.trust' in httpd and b'restart_privoxy' in httpd
    checks['save_failure_feedback'] = ('function privoxySaveFailed()' in page and
                                       '<#Service_Privoxy_Alert_Save#>' in page and
                                       b'privoxySaveFailed' in httpd)
    handler = (args.trunk / 'user/httpd/web_ex.c').read_text(encoding='utf-8')
    apply_start = handler.find('result = validate_asp_apply(wp, sid);')
    failure_branch = handler.find('if (privoxy_storage_save_failed)', apply_start)
    success_branch = handler.find('done_committing();</script>', apply_start)
    checks['save_failure_apply_order'] = (
        apply_start >= 0 and apply_start < failure_branch < success_branch and
        'privoxy_storage_save_failed = 1;' in handler and
        'if(parent.privoxySaveFailed)parent.privoxySaveFailed()' in handler and
        'restart_needed_bits = 0;' in handler[failure_branch:success_branch] and
        'restart_needed_extended = 0;' in handler[failure_branch:success_branch] and
        'return 0;' in handler[failure_branch:success_branch])
    checks['rc'] = b'/usr/bin/privoxy.sh' in rc and b'restart_privoxy' in rc
    queue = [binary]
    visited = set()
    missing = []
    while queue:
        path = queue.pop()
        if path in visited:
            continue
        visited.add(path)
        needed = re.findall(r'\(NEEDED\).*\[([^\]]+)\]', subprocess.check_output(['readelf', '-d', str(path)], text=True))
        for name in needed:
            candidates = [target(prefix + name) for prefix in ['/lib/', '/usr/lib/']]
            dependency = next((p for p in candidates if p.is_file()), None)
            if dependency is None:
                missing.append(name)
            else:
                queue.append(dependency)
    checks['shared_libraries'] = not missing
    details['missing_libraries'] = sorted(set(missing))
    program = subprocess.check_output(['readelf', '-l', str(binary)], text=True)
    interpreters = re.findall(r'Requesting program interpreter:\s*([^\]]+)', program)
    checks['loader'] = len(interpreters) == 1 and target(interpreters[0]).is_file()
except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
    checks['inspection_completed'] = False
    details['error'] = str(error)
args.report.write_text(json.dumps({'scope': 'Privoxy image packaging; runtime unverified', 'checks': checks, 'details': details}, indent=2) + '\n')
if not all(checks.values()):
    raise SystemExit('Privoxy image check failed: ' + ', '.join(name for name, value in checks.items() if not value))
print('Privoxy ROMFS and library checks passed; runtime remains unverified')
