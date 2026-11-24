from pathlib import Path
import hashlib
import sys
import runpy
import tempfile
here=Path(__file__).resolve().parent
module=runpy.run_path(str(here/'stage-classic-config-romfs.py'));stage=module['stage'];snapshot=module['snapshot']
metadata={'board':'WR1200JS',**{key:True for key in ('edit_startup_attempt_prepared','view_startup_attempt_prepared','native_capabilities_verified','http_view_bound','http_edit_bound','http_runtime_toggle_bound','http_bound')}}
# ABI runs on Ubuntu22/Python3.10, which has no file_digest. Exercise that
# environment even when the local interpreter provides the newer helper.
if hasattr(hashlib,'file_digest'):delattr(hashlib,'file_digest')
with tempfile.TemporaryDirectory(prefix='wr-classic-romfs-') as directory:
    root=Path(directory);(root/'www').mkdir();page=root/'www/Advanced_IoT_Content.asp'
    page.write_bytes((here/'classic-pending.asp').read_bytes());page.chmod(0o644)
    state=root/'www/state.js'
    original_state=(Path(sys.argv[1]).read_bytes() if len(sys.argv)>1 else
                    b'function show_banner() {}\n// id="wifi2_b" id="wifi5_b" id="wifi2_b_g" id="wifi5_b_g"\n')
    state.write_bytes(original_state);state.chmod(0o640)
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
    state.write_bytes(original_state.replace(b'function show_banner(',b'function changed_banner('))
    changed=snapshot(root)
    try:stage(root,metadata)
    except ValueError:pass
    else:raise AssertionError('Changed native banner accepted')
    assert snapshot(root)==changed
    state.write_bytes(original_state)
    result=stage(root,metadata)
    assert result['classic_configuration_staged'] and result['activation_control']
    assert result['classic_navigation_staged']
    assert set(result['sha256'])=={'www/Advanced_IoT_Content.asp','www/classic-iot-config.js','www/state.js','www/classic-iot-navigation.js'}
    assert state.read_bytes().startswith(original_state) and state.stat().st_mode&0o777==0o640
    assert state.read_text().count("s.src = '/classic-iot-navigation.js'")==1
    assert (root/'www/classic-iot-navigation.js').read_bytes()==(here/'classic-navigation.js').read_bytes()
    assert (root/'www/classic-iot-navigation.js').stat().st_mode&0o777==0o644
    assert (root/'www/unrelated').read_text()=='keep'
    assert (root/'www/classic-iot-config.js').read_bytes()==(here/'classic-config.js').read_bytes()
    assert 'wrIotConfig.init()' in page.read_text()
    assert page.read_text().count('WPA2-Personal (PSK), AES (CCMP)') == 1
    assert '<label for="iot-action">Пароль</label>' in page.read_text()
    assert '<p style="padding-left: 15px;"><a class="btn" href="/index.asp">' in page.read_text()
    before=snapshot(root)
    try:stage(root,metadata)
    except ValueError:pass
    else:raise AssertionError('Repeated staging accepted')
    assert snapshot(root)==before
    (root/'www/classic-iot-config.js').unlink();page.unlink()
    (root/'www/classic-iot-navigation.js').unlink();state.write_bytes(original_state)
    result=stage(root,metadata)
    assert page.is_file() and (root/'www/unrelated').read_text()=='keep'
    assert page.stat().st_mode&0o777==0o644
print('PASS Classic ROMFS configuration/navigation: complete typed gates, exact page/banner/radio anchors, unchanged original state prefix and modes, unrelated entries preserved, drift/duplicate refused before writes; '+('native Classic source, host staging only' if len(sys.argv)>1 else 'synthetic ROMFS only'))
