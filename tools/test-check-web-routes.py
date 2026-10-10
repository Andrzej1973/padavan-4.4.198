#!/usr/bin/env python3
"""Fixture tests for check-web-routes.py; needs only Python, no firmware tree."""
import importlib.util
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True  # Keep tools/ free of __pycache__.
spec = importlib.util.spec_from_file_location('routes', Path(__file__).with_name('check-web-routes.py'))
routes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(routes)

# httpd.c matcher semantics.
assert routes.match('**.css', 'bootstrap/css/main.css')
assert routes.match('*.css', 'main.css') and not routes.match('*.css', 'bootstrap/main.css')
assert routes.match('**.asp*', 'index.asp?x=1') and routes.match('apply.cgi*', 'apply.cgi')
assert routes.match('a.js|b.js', 'b.js') and not routes.match('a.js|b.js', 'c.js')
assert routes.match('syslog.t?t', 'syslog.txt') and not routes.match('syslog.t?t', 'syslog.tt')
assert not routes.match('jquery.js', 'jquery.json') and not routes.match('**.js', 'dot.json')

WEB_EX = r'''
struct mime_handler mime_handlers[] = {
	{ "**.css", "text/css", NULL, NULL, do_file, 0 },
#if defined(APP_ARIA)
	{ "**.woff", "application/font-woff", NULL, NULL, do_file, 0 },
#else
	{ "**.ttf", "font/ttf", NULL, NULL, do_file, 0 },
#endif
#if defined (APP_ARIA) && !defined(APP_SCUT)
	{ "**.woff2", "application/font-woff", NULL, NULL, do_file, 0 },
#endif
#ifdef BOARD_WR1200JS
	{ "wr_devices.json", "application/json", no_cache_IE, NULL, do_wr_devices_json, 1 },
#endif
	{ "**.asp*", "text/html", no_cache_IE, do_html_apply_post, do_ej, 1 },
	{ "**.js",  "text/javascript", no_cache_IE, NULL, do_ej, 1 },
	{ NULL, NULL, NULL, NULL, NULL, 0 }
};
'''
CFLAGS = 'ifeq ($(CONFIG_FIRMWARE_INCLUDE_ARIA),y)\nCFLAGS += -DAPP_ARIA\nendif\n' \
         'ifeq ($(CONFIG_FIRMWARE_INCLUDE_SCUTCLIENT),y)\nCFLAGS += -DAPP_SCUT\nendif\n'


def tree(root, config, files):
    (root / 'user/httpd').mkdir(parents=True)
    (root / 'user/shared').mkdir(parents=True)
    (root / 'user/httpd/web_ex.c').write_text(WEB_EX)
    (root / 'user/shared/cflags.mk').write_text(CFLAGS)
    (root / '.config').write_text(config)
    for name in files + ['EN.header', 'UK.dict']:
        (root / 'romfs/www' / name).parent.mkdir(parents=True, exist_ok=True)
        (root / 'romfs/www' / name).write_text('x')
    return routes.check(root, root / 'romfs/www', root / '.config', [])


with tempfile.TemporaryDirectory() as temp:
    base = Path(temp)
    # Every installed asset routed; dictionaries are internal and exempt.
    result = tree(base / 'ok', 'CONFIG_FIRMWARE_INCLUDE_ARIA=y\n',
                  ['index.asp', 'general.js', 'bootstrap/css/main.css', 'font.woff', 'font.woff2'])
    assert result['unrouted'] == [] and result['files'] == 5, result
    assert result['routed']['font.woff2'] == '**.woff2'
    # Stubby's provider list: present in ROMFS, but no table entry serves JSON.
    result = tree(base / 'json', 'CONFIG_FIRMWARE_INCLUDE_ARIA=y\n', ['index.asp', 'dot.json'])
    assert result['unrouted'] == ['dot.json'], result
    # A route compiled out by the .config is a 404 even though the file ships.
    result = tree(base / 'off', '# CONFIG_FIRMWARE_INCLUDE_ARIA is not set\n', ['font.woff', 'font.ttf'])
    assert result['unrouted'] == ['font.woff'], result
    result = tree(base / 'and', 'CONFIG_FIRMWARE_INCLUDE_ARIA=y\nCONFIG_FIRMWARE_INCLUDE_SCUTCLIENT=y\n',
                  ['font.woff2'])
    assert result['unrouted'] == ['font.woff2'], result
    # Unknown board macros are reported as assumed undefined, never guessed.
    assert result['assumed_undefined'] == ['BOARD_WR1200JS'], result
    assert routes.check(base / 'and', base / 'and/romfs/www', base / 'and/.config',
                        ['BOARD_WR1200JS'])['assumed_undefined'] == []

print('PASS web route checker: httpd matcher, config-resolved conditionals and unrouted JSON detection')
