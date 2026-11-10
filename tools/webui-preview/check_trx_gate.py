#!/usr/bin/env python3
"""Exercise final-content gate with actual SquashFS fixtures, not firmware builds."""
import tempfile
import subprocess
from pathlib import Path
from check_trx_contents import check

with tempfile.TemporaryDirectory(prefix='wr-trx-gate-test-') as scratch:
    root=Path(scratch)
    romfs=root/'romfs'
    names=['www/modern/'+n for n in ('index.html','app.js','wifi.js','shared-wifi.js','wifi-schema.json','styles.css','favicon.svg')]
    names+=['sbin/rc','www/wr-band-status.js','www/Advanced_WAdvanced2g_Content.asp',
            'www/Advanced_Services_Content.asp', 'www/EN.dict', 'www/UK.dict', 'www/RU.dict',
            'usr/sbin/httpd','usr/sbin/nfqws2','usr/sbin/zapret2',
            *('usr/share/zapret2/'+n for n in ('zapret-lib.lua','zapret-antidpi.lua','zapret-auto.lua')),
            'usr/share/licenses/zapret2/LICENSE.txt']
    for name in names:
        path=romfs/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(name)
    binary=romfs/'usr/sbin/httpd'
    binary.chmod(0o755)
    squash=root/'fixture.sqfs'
    subprocess.run(['mksquashfs',str(romfs),str(squash),'-noappend','-processors','1','-no-progress'],check=True,stdout=subprocess.DEVNULL)
    image=root/'fixture.trx'
    image.write_bytes(b'fixture header'+squash.read_bytes())
    assert check(image,romfs)['squashfs_offset']==14
    # A valid filesystem with a required component omitted must fail closed.
    missing=romfs/'usr/sbin/nfqws2'
    saved_missing=missing.read_bytes()
    missing.unlink()
    incomplete=root/'incomplete.sqfs'
    subprocess.run(['mksquashfs',str(romfs),str(incomplete),'-noappend','-processors','1','-no-progress'],check=True,stdout=subprocess.DEVNULL)
    missing.write_bytes(saved_missing)
    original_image=image.read_bytes()
    image.write_bytes(b'fixture header'+incomplete.read_bytes())
    try:
        check(image,romfs)
        raise AssertionError('missing nfqws2 accepted')
    except FileNotFoundError:
        pass
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
print('PASS final-content gate real SquashFS fixtures: offset/content/mode/missing filesystem; scratch removed')
