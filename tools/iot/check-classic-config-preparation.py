from pathlib import Path
import json
import runpy
import tempfile
here=Path(__file__).resolve().parent
prepare=runpy.run_path(str(here/'prepare-classic-config.py'))['prepare']
with tempfile.TemporaryDirectory(prefix='wr-classic-config-') as directory:
    source=Path(directory);web=source/'trunk/user/www/n56u_ribbon_fixed';web.mkdir(parents=True)
    http=source/'trunk/user/httpd';http.mkdir(parents=True)
    page=web/'Advanced_IoT_Content.asp';original=(here/'classic-pending.asp').read_bytes();page.write_bytes(original)
    metadata={'board':'WR1200JS','edit_startup_attempt_prepared':True,'view_startup_attempt_prepared':True,
              'native_capabilities_verified':True,'http_view_bound':True,'http_edit_bound':True,'http_runtime_toggle_bound':True}
    report=source/'iot-edit-view-source.json'
    routes='\n'.join('{ "wr_iot_edit_'+suffix+'.cgi", "application/json", no_cache_IE, wr_iot_http_apply_input, wr_iot_http_edit_'+suffix+'_output, 1 }' for suffix in ('ram','auto','save','runtime'))
    (http/'web_ex.c').write_text(routes)
    for key in ('native_capabilities_verified','http_view_bound','http_edit_bound','http_runtime_toggle_bound'):
        invalid=dict(metadata);invalid[key]=False;report.write_text(json.dumps(invalid))
        try:prepare(source)
        except ValueError:pass
        else:raise AssertionError('Incomplete integration must refuse')
        assert page.read_bytes()==original and not (web/'classic-iot-config.js').exists()
    report.write_text(json.dumps(metadata));result=prepare(source)
    text=page.read_text()
    assert 'WR_IOT_CLASSIC_Pending' not in text and 'wrIotConfig.init()' in text
    assert text.count('/classic-iot-config.js')==1 and 'type="password"' in text
    assert result['activation_control'] and not result['runtime_verified']
    before=page.read_bytes()
    try:prepare(source)
    except ValueError:pass
    else:raise AssertionError('Repeated install must refuse')
    assert page.read_bytes()==before
print('PASS Classic candidate preparation: exact baseline, capability/four HTTP route gates before writes, complete config/runtime form, duplicate refusal; source only, no runtime acceptance')
