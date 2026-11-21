import argparse
import hashlib
import json
from pathlib import Path

def prepare(source):
    source=Path(source);local=Path(__file__).resolve().parent
    web=source/'trunk/user/www/n56u_ribbon_fixed'
    page=web/'Advanced_IoT_Content.asp';script=web/'classic-iot-config.js'
    report_path=source/'iot-classic-config.json'
    if page.is_symlink() or script.exists() or script.is_symlink() or report_path.exists():
        raise ValueError('Existing or linked Classic configuration destination')
    original=page.read_bytes()
    if original!=(local/'classic-pending.asp').read_bytes():
        raise ValueError('Classic pending page differs; preserve existing work')
    metadata=json.loads((source/'iot-edit-view-source.json').read_text())
    if metadata.get('board')!='WR1200JS' or not all(metadata.get(key) is True for key in (
            'edit_startup_attempt_prepared','view_startup_attempt_prepared','native_capabilities_verified','http_view_bound','http_edit_bound','http_runtime_toggle_bound')):
        raise ValueError('Complete prepared IoT edit/view source required')
    http=(source/'trunk/user/httpd/web_ex.c').read_text()
    for suffix in ('ram','auto','save','runtime'):
        route='{ "wr_iot_edit_'+suffix+'.cgi", "application/json", no_cache_IE, wr_iot_http_apply_input, wr_iot_http_edit_'+suffix+'_output, 1 }'
        if http.count(route)!=1:raise ValueError('Missing authenticated edit route: '+suffix)
    text=original.decode()
    anchor='<div class="alert alert-info"><#WR_IOT_CLASSIC_Pending#></div>'
    if text.count(anchor)!=1 or text.count('show_footer(); }')!=1:raise ValueError('Classic page anchors changed')
    text=text.replace('<script>','<script src="/classic-iot-config.js"></script>\n<script>',1)
    text=text.replace('show_footer(); }','show_footer(); wrIotConfig.init(); }',1)
    text=text.replace(anchor,(local/'classic-config-form.html').read_text(),1)
    pending={page:text.encode(),script:(local/'classic-config.js').read_bytes()}
    report={'board':'WR1200JS','configuration_form_prepared':True,'activation_control':True,
            'target_verified':False,'runtime_verified':False,
            'files':{str(path.relative_to(source)):hashlib.sha256(data).hexdigest() for path,data in pending.items()}}
    for path,data in pending.items():path.write_bytes(data)
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);args=parser.parse_args()
    prepare(args.source)
    print('PASS Classic configuration candidate staged; activation and target/device verification remain separate')
