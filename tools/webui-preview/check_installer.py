#!/usr/bin/env python3
"""Verify installer preflight errors preserve source and a clean retry works."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-modern-installer-') as scratch:
    work = Path(scratch)
    tools = work / 'tools'
    preview = tools / 'webui-preview'
    shutil.copytree(HERE, preview, ignore=shutil.ignore_patterns('__pycache__'))
    (tools / 'shared-wifi').mkdir()
    shutil.copyfile(HERE.parent / 'shared-wifi/ui.js', tools / 'shared-wifi/ui.js')
    source = work / 'source'
    httpd = source / 'trunk/user/httpd'
    httpd.mkdir(parents=True)
    www = source / 'trunk/user/www'
    www.mkdir()
    web = httpd / 'web_ex.c'
    original = '#include <stdio.h>\n#include \"common.h\"\n#include \"httpd.h\"\nstruct mime_handler mime_handlers[] = {\n};\n'
    web.write_text(original)
    installer = preview / 'prepare-production.py'

    def run():
        return subprocess.run([sys.executable, str(installer), str(source)], capture_output=True, text=True)

    for asset, old, new in [
        ('app.js', '/api/dashboard.json', '/changed.json'),
        ('wifi.js', "fetch('/wifi-schema.json'", "fetch('/changed.json'"),
        ('wifi-schema.json', '"demo": true', '"demo": false'),
    ]:
        path = preview / 'public' / asset
        saved = path.read_bytes()
        path.write_text(saved.decode().replace(old, new))
        result = run()
        assert result.returncode != 0, asset
        assert web.read_text() == original, asset
        assert not (www / 'modern').exists(), asset
        path.write_bytes(saved)
    path = preview / 'public/favicon.svg'
    saved = path.read_bytes()
    path.unlink()
    assert run().returncode != 0
    assert web.read_text() == original
    assert not (www / 'modern').exists()
    path.write_bytes(saved)
    result = run()
    assert result.returncode == 0, result.stderr
    subprocess.run([sys.executable, str(preview / 'check-production.py'), str(source)], check=True)
    # Exercise the image gate with a synthetic ROMFS, including two failures.
    import importlib.util
    spec = importlib.util.spec_from_file_location('modern_image', HERE / 'check_image.py')
    image = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(image)
    romfs = source / 'trunk/romfs'
    shutil.copytree(www, romfs / 'www')
    binary = romfs / 'usr/sbin/httpd'
    binary.parent.mkdir(parents=True)
    routes = ['wr_modern.json', *('modern/' + n.name for n in (www / 'modern').iterdir())]
    binary.write_bytes(b'\0'.join(r.encode() for r in routes) + b'\0')
    image.check(source)  # Synthetic literals do not constitute a target build.
    asset = romfs / 'www/modern/app.js'
    saved = asset.read_bytes()
    asset.write_bytes(saved + b'changed')
    try:
        image.check(source)
        raise AssertionError('image mismatch accepted')
    except ValueError as error:
        assert 'asset differs' in str(error)
    asset.write_bytes(saved)
    binary.write_bytes(b'wr_modern.json\0')
    try:
        image.check(source)
        raise AssertionError('missing compiled asset route accepted')
    except ValueError as error:
        assert 'Missing compiled' in str(error)
    installed = web.read_bytes()
    assert run().returncode != 0
    assert web.read_bytes() == installed
print('PASS installer preflight: three changed anchors + missing asset leave source untouched; clean retry and overwrite refusal; image gate positive/negative cases; scratch removed')
