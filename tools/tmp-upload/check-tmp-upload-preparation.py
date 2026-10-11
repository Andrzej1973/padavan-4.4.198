#!/usr/bin/env python3
"""Exercise preparation on an isolated copy of actual donor files."""
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile

spec = importlib.util.spec_from_file_location('tmp_prepare', Path(__file__).with_name('prepare-tmp-upload.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
donor = Path(sys.argv[1])
files = ['trunk/user/httpd/web_ex.c'] + [
    'trunk/user/www/n56u_ribbon_fixed/' + name for name in
    ('bit_action.asp', 'Advanced_FirmwareUpgrade_Content.asp')
] + ['trunk/user/www/dict/' + name for name in ('EN.footer', 'UK.dict', 'RU.dict')]
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    for name in files:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(donor / name, target)
    module.prepare(root)
    source = (root / files[0]).read_text(encoding='utf-8')
    assert 'if (get_login_safe()) result = wr_tmp_upload_increase' in source
    assert 'window.wrTmpResult=%d;window.wrTmpLimit=%llu;' in source
    assert 'system("mount -t tmpfs -o remount,rw,size=50M tmpfs /tmp")' not in source
    response = (root / files[1]).read_text(encoding='utf-8')
    assert response.index('alert(text') < response.index('setTimeout(')
    upgrade = (root / files[2]).read_text(encoding='utf-8')
    assert 'style="width:50px display:none;"' not in upgrade
    assert "submitInternet('bigtmp');" in upgrade
    for name in files[3:]:
        content = (root / name).read_text(encoding='utf-8')
        for key in ('TMP_btn', 'FW_desc7', 'TMP_result_ok', 'TMP_result_memory', 'TMP_result_failed'):
            assert sum(line.startswith(key + '=') for line in content.splitlines()) == 1
    before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
    try:
        module.prepare(root)
    except ValueError:
        pass
    else:
        raise AssertionError('Repeated preparation must reject already patched input')
    assert before == {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
print('PASS: tmp upload source, feedback, labels, button and repeated-preparation guard')
