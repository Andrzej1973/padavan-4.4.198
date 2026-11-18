from pathlib import Path
import hashlib
import runpy
import tempfile
here=Path(__file__).resolve().parent
module=runpy.run_path(str(here/'stage-classic-config-romfs.py'));stage=module['stage'];snapshot=module['snapshot']
metadata={'board':'WR1200JS',**{key:True for key in ('edit_startup_attempt_prepared','view_startup_attempt_prepared','native_capabilities_verified','http_view_bound','http_edit_bound','http_bound')}}
# ABI runs on Ubuntu22/Python3.10, which has no file_digest. Exercise that
# environment even when the local interpreter provides the newer helper.
if hasattr(hashlib,'file_digest'):delattr(hashlib,'file_digest')
with tempfile.TemporaryDirectory(prefix='wr-classic-romfs-') as directory:
    root=Path(directory);(root/'www').mkdir();page=root/'www/Advanced_IoT_Content.asp'
    page.write_bytes((here/'classic-pending.asp').read_bytes());page.chmod(0o644)
    (root/'www/unrelated').write_text('keep')
    content=bytes(range(256))*8193
    (root/'www/large-unrelated').write_bytes(content)
    before=snapshot(root)
    assert before['www/large-unrelated']['sha256']==hashlib.sha256(content).hexdigest()
    for key in metadata:
        broken=dict(metadata);broken[key]=False
        try:stage(root,broken)
        except ValueError:pass
        else:raise AssertionError('Missing capability accepted')
        assert snapshot(root)==before
    result=stage(root,metadata)
    assert result['classic_configuration_staged'] and not result['activation_control']
    assert (root/'www/unrelated').read_text()=='keep'
    assert (root/'www/classic-iot-config.js').read_bytes()==(here/'classic-config.js').read_bytes()
    assert 'wrIotConfig.init()' in page.read_text()
    before=snapshot(root)
    try:stage(root,metadata)
    except ValueError:pass
    else:raise AssertionError('Repeated staging accepted')
    assert snapshot(root)==before
    (root/'www/classic-iot-config.js').unlink();page.unlink()
    result=stage(root,metadata)
    assert page.is_file() and (root/'www/unrelated').read_text()=='keep'
    assert page.stat().st_mode&0o777==0o644
print('PASS Classic ROMFS staging: complete typed gates, exact page and absent script required, unrelated entries/modes preserved, duplicate refused before mutation; synthetic ROMFS only')
