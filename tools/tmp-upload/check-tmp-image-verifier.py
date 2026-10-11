#!/usr/bin/env python3
"""Synthetic verifier fixtures; not image verification evidence."""
import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
spec = importlib.util.spec_from_file_location('image_verify', Path(__file__).with_name('verify-tmp-upload-image.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
source = Path(sys.argv[1]) / 'trunk/user/www'
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    web = root / 'www'
    web.mkdir()
    (root / 'usr/sbin').mkdir(parents=True)
    for name in ('bit_action.asp', 'Advanced_FirmwareUpgrade_Content.asp'):
        shutil.copyfile(source / 'n56u_ribbon_fixed' / name, web / name)
    page = web / 'Advanced_FirmwareUpgrade_Content.asp'
    page.write_text(page.read_text(encoding='utf-8').replace('style="width:50px display:none;"', 'style="margin-left:8px;"'), encoding='utf-8')
    for language in ('UK', 'RU'):
        shutil.copyfile(source / 'dict' / (language + '.dict'), web / (language + '.dict'))
    shutil.copyfile(source / 'dict/EN.footer', web / 'EN.dict')
    binary = root / 'usr/sbin/httpd'
    marker = b'window.wrTmpResult=%d;window.wrTmpLimit=%llu;'
    binary.write_bytes(marker)
    assert module.verify(root).startswith('PASS')
    binary.write_bytes(b'old httpd')
    try:
        module.verify(root)
    except ValueError:
        pass
    else:
        raise AssertionError('Missing linked result accepted')
    binary.write_bytes(marker)
    dictionary = web / 'UK.dict'
    dictionary.write_text(dictionary.read_text(encoding='utf-8') + '\nTMP_btn=duplicate\n', encoding='utf-8')
    try:
        module.verify(root)
    except ValueError:
        pass
    else:
        raise AssertionError('Duplicate translation accepted')
print('PASS: synthetic verifier fixtures, not a firmware image')
