#!/usr/bin/env python3
"""Logic fixtures: synthetic ELF headers and mocked readelf, not target execution."""
import importlib.util
import struct
import tempfile
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('closure', Path(__file__).with_name('verify-package-closure.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def expect_error(action, message):
    try:
        action()
    except ValueError as error:
        assert message in str(error), str(error)
    else:
        raise AssertionError('Expected rejection: ' + message)


with tempfile.TemporaryDirectory(prefix='wr-steering-closure-', dir=Path.cwd()) as temporary:
    root = Path(temporary)
    assert root.resolve().is_relative_to(Path.cwd().resolve())
    staged, image = root / 'candidate', root / 'image'
    for folder in (staged / 'usr/sbin', image / 'lib', image / 'usr'):
        folder.mkdir(parents=True, exist_ok=True)
    elf = bytearray(52)
    elf[:7] = b'\x7fELF\x01\x01\x01'
    struct.pack_into('<H', elf, 16, 3)
    struct.pack_into('<H', elf, 18, 8)
    for binary in ('wr-band-steering', 'wr-band-steering-ctl'):
        (staged / 'usr/sbin' / binary).write_bytes(elf)
    for library in ('libc-real.so', 'libm.so.0', 'ld-real.so'):
        (image / 'lib' / library).write_bytes(elf)
    links = {
        image / 'lib/libc.so.0': '/lib/libc-real.so',
        image / 'lib/ld.so.0': 'ld-real.so',
        image / 'usr/lib': '/lib',
    }
    mode = [0]

    def readelf(command, **kwargs):
        assert kwargs['env']['LC_ALL'] == 'C'
        path = Path(command[2])
        candidate = path.is_relative_to(staged)
        if command[1] == '-d':
            if candidate:
                if mode[0] == 1:
                    return '(NEEDED) Shared library: [missing.so]\n'
                if mode[0] == 2:
                    return '(RUNPATH) Library runpath: [/host/lib]\n'
                if mode[0] == 4:
                    return '(NEEDED) Shared library: [usr-only.so]\n'
                return '(NEEDED) Shared library: [libc.so.0]\n'
            if path.name == 'libc-real.so':
                return '(NEEDED) Shared library: [libm.so.0]\n'
            if path.name == 'libm.so.0':
                return '(NEEDED) Shared library: [libc.so.0]\n'
            return ''
        assert command[1] == '-l'
        return '[Requesting program interpreter: /lib/ld.so.0]\n' if candidate and mode[0] != 3 else ''

    with patch.object(Path, 'is_symlink', lambda p: p in links), \
         patch.object(module.os, 'readlink', lambda p: links[Path(p)]), \
         patch.object(module.subprocess, 'check_output', readelf):
        assert module.resolve_image(image, 'usr/lib/libc.so.0') == image / 'lib/libc-real.so'
        result = module.verify(staged, image, 'mock-readelf')
        assert len(result) == 5 and 'image:lib/ld-real.so' in result
        assert result['image:lib/libc-real.so']['needed'] == ['libm.so.0']
        (staged / 'usr/sbin/rc').write_bytes(elf)
        rc_result = module.verify(staged, image, 'mock-readelf', ['usr/sbin/rc'])
        assert len(rc_result) == 4 and 'candidate:usr/sbin/rc' in rc_result
        expect_error(lambda: module.verify(staged, image, 'mock-readelf', []),
                     'No candidate')
        for invalid in ('/usr/sbin/rc', '../rc', 'usr/../rc'):
            expect_error(lambda: module.verify(staged, image, 'mock-readelf', [invalid]),
                         'relative to staging root')
        (image / 'otherlib').mkdir()
        (image / 'otherlib/usr-only.so').write_bytes(elf)
        links[image / 'usr/lib'] = '/otherlib'
        mode[0] = 4
        # The first search directory is missing this library; usr/lib is a
        # directory symlink whose absolute target belongs to the image.
        alternate = module.verify(staged, image, 'mock-readelf')
        assert 'image:otherlib/usr-only.so' in alternate
        links[image / 'usr/lib'] = '/lib'
        mode[0] = 1
        expect_error(lambda: module.verify(staged, image, 'mock-readelf'), 'Missing missing.so')
        mode[0] = 2
        expect_error(lambda: module.verify(staged, image, 'mock-readelf'), 'runtime search path')
        mode[0] = 3
        expect_error(lambda: module.verify(staged, image, 'mock-readelf'), 'no interpreter')
        mode[0] = 0
        links[image / 'escape'] = '../../outside'
        expect_error(lambda: module.resolve_image(image, 'escape'), 'escapes root')
        links[image / 'loop'] = '/loop'
        expect_error(lambda: module.resolve_image(image, 'loop'), 'symlink loop')
        bad = bytearray(elf)
        struct.pack_into('<H', bad, 18, 62)
        (staged / 'usr/sbin/wr-band-steering').write_bytes(bad)
        expect_error(lambda: module.verify(staged, image, 'mock-readelf'), 'ELF32 MIPS')
        (staged / 'usr/sbin/wr-band-steering').write_bytes(elf)
        bad = bytearray(elf)
        struct.pack_into('<H', bad, 16, 1)
        (staged / 'usr/sbin/wr-band-steering').write_bytes(bad)
        expect_error(lambda: module.verify(staged, image, 'mock-readelf'), 'ELF type')
        (staged / 'usr/sbin/wr-band-steering').write_bytes(elf)
        assert len(module.verify(staged, image, 'mock-readelf')) == 5

print('PASS closure logic: recursive dependencies, loader, missing files, wrong ELF, image-root symlinks, loops and fallback search; readelf mocked')
