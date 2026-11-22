#!/usr/bin/env python3
"""Exercise final-content gate with actual SquashFS fixtures, not firmware builds."""
import tempfile
import shutil
import subprocess
from pathlib import Path
from check_trx_contents import check

with tempfile.TemporaryDirectory(prefix='wr-trx-gate-test-') as scratch:
    root=Path(scratch)
    romfs=root/'romfs'
    names=['www/modern/'+n for n in ('index.html','app.js','wifi.js','shared-wifi.js','wifi-schema.json','styles.css','favicon.svg')]
    names+=['sbin/rc','www/wr-band-status.js', 'www/index.asp','www/Advanced_WAdvanced2g_Content.asp',
            'www/Advanced_Services_Content.asp', 'www/EN.dict', 'www/UK.dict', 'www/RU.dict',
            'usr/sbin/httpd','usr/sbin/nfqws2','usr/sbin/zapret2',
            *('usr/share/zapret2/'+n for n in ('zapret-lib.lua','zapret-antidpi.lua','zapret-auto.lua')),
            'usr/share/licenses/zapret2/LICENSE.txt']
    for name in names:
        path=romfs/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(name)
    (romfs/'www/modern/wifi.js').write_text(
        'const routes = ["/status_lanlink.asp", "/index.asp", "/index.asp"];')
    binary=romfs/'usr/sbin/httpd'
    binary.chmod(0o755)
    squash=root/'fixture.sqfs'
    subprocess.run(['mksquashfs',str(romfs),str(squash),'-noappend','-processors','1','-no-progress'],check=True,stdout=subprocess.DEVNULL)
    image=root/'fixture.trx'
    image.write_bytes(b'fixture header'+squash.read_bytes())
    report = check(image, romfs)
    assert report['squashfs_offset'] == 14
    assert report['modern_asp_reference_literals'] == {
        'www/modern/wifi.js': ['/index.asp', '/status_lanlink.asp'],
    }
    # A valid filesystem missing a required entry must fail closed.
    original_image = image.read_bytes()
    for index, name in enumerate(('usr/sbin/nfqws2', 'www/index.asp')):
        missing = romfs / name
        saved_missing = missing.read_bytes()
        missing.unlink()
        incomplete = root / f'incomplete-{index}.sqfs'
        subprocess.run(['mksquashfs', str(romfs), str(incomplete), '-noappend',
                        '-processors', '1', '-no-progress'], check=True,
                       stdout=subprocess.DEVNULL)
        missing.write_bytes(saved_missing)
        image.write_bytes(b'fixture header' + incomplete.read_bytes())
        try:
            check(image, romfs)
        except FileNotFoundError as error:
            assert Path(error.filename).as_posix().endswith(name)
        else:
            raise AssertionError('Missing required file accepted: ' + name)
    image.write_bytes(original_image)
    saved=binary.read_bytes()
    binary.write_bytes(b'corrupt')
    try:
        check(image,romfs)
        raise AssertionError('content mismatch accepted')
    except ValueError as error:
        assert 'differs' in str(error)
    binary.write_bytes(saved)
    binary.chmod(0o644)
    try:
        check(image,romfs)
        raise AssertionError('mode mismatch accepted')
    except ValueError as error:
        assert 'mode differs' in str(error)
    image.write_bytes(b'no filesystem')
    try:
        check(image,romfs)
        raise AssertionError('missing filesystem accepted')
    except ValueError as error:
        assert 'Expected one' in str(error)
    (romfs/'www/state.js').write_text('Classic banner')
    try:
        image.write_bytes(original_image)
        check(image, romfs, classic_only=True)
    except ValueError as error:
        assert 'contains Modern or Hybrid assets' in str(error)
    else:
        raise AssertionError('Modern assets accepted in Classic-only image')
    shutil.rmtree(romfs/'www/modern')
    binary.chmod(0o755)
    classic = root/'classic.sqfs'
    subprocess.run(['mksquashfs', str(romfs), str(classic), '-noappend',
                    '-processors', '1', '-no-progress'], check=True,
                   stdout=subprocess.DEVNULL)
    image.write_bytes(b'fixture header' + classic.read_bytes())
    classic_report = check(image, romfs, classic_only=True)
    assert classic_report['classic_only_verified']
    assert 'www/state.js' in classic_report['files_sha256']
    # httpd route registration uses paths without the leading slash.
    binary.write_bytes(b'modern/index.html\0')
    leaked = root/'leaked-route.sqfs'
    subprocess.run(['mksquashfs', str(romfs), str(leaked), '-noappend',
                    '-processors', '1', '-no-progress'], check=True,
                   stdout=subprocess.DEVNULL)
    image.write_bytes(b'fixture header' + leaked.read_bytes())
    try:
        check(image, romfs, classic_only=True)
    except ValueError as error:
        assert 'contains a Modern/Hybrid route: usr/sbin/httpd' in str(error)
    else:
        raise AssertionError('Modern route accepted in Classic-only image')
print('PASS final-content gate real SquashFS fixtures: offset/content/mode/missing filesystem; scratch removed')
