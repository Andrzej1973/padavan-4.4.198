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
    original = 'struct mime_handler mime_handlers[] = {\n};\n'
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
    installed = web.read_bytes()
    assert run().returncode != 0
    assert web.read_bytes() == installed
print('PASS installer preflight: three changed anchors + missing asset leave source untouched; clean retry and overwrite refusal; scratch removed')
