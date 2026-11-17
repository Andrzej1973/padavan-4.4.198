import hashlib
import json
import runpy
from pathlib import Path
here=Path(__file__).resolve().parent
snapshot=runpy.run_path(str(here/'stage-candidate-romfs.py'))['snapshot']

def stage(romfs,metadata):
    romfs=Path(romfs)
    required=('edit_startup_attempt_prepared','view_startup_attempt_prepared','native_capabilities_verified','http_view_bound','http_edit_bound','http_bound')
    if metadata.get('board')!='WR1200JS' or any(metadata.get(key) is not True for key in required):
        raise ValueError('Complete edit/view source metadata required')
    before=snapshot(romfs)
    page='www/Advanced_IoT_Content.asp';script='www/classic-iot-config.js'
    if before.get('www',{}).get('type')!='directory' or (page in before and before[page]['type']!='file') or script in before:
        raise ValueError('Regular or absent Classic page and absent script required')
    original=(here/'classic-pending.asp').read_bytes()
    if page in before and (romfs/page).read_bytes()!=original:raise ValueError('Classic pending page differs')
    text=original.decode()
    text=text.replace('<script>','<script src="/classic-iot-config.js"></script>\n<script>',1)
    text=text.replace('show_footer(); }','show_footer(); wrIotConfig.init(); }',1)
    text=text.replace('<div class="alert alert-info"><#WR_IOT_CLASSIC_Pending#></div>',(here/'classic-config-form.html').read_text(),1)
    payload={page:text.encode(),script:(here/'classic-config.js').read_bytes()}
    for name,data in payload.items():(romfs/name).write_bytes(data)
    (romfs/script).chmod(0o644)
    if page not in before:(romfs/page).chmod(0o644)
    after=snapshot(romfs)
    if set(after)!=set(before)|{script,page}:raise ValueError('Unexpected Classic ROMFS entries')
    for name,record in before.items():
        if name!=page and after[name]!=record:raise ValueError('Unrelated ROMFS entry changed: '+name)
    if page in before and before[page]['mode']!=after[page]['mode']:raise ValueError('Classic page mode changed')
    return {'board':'WR1200JS','classic_configuration_staged':True,'activation_control':False,
            'sha256':{name:hashlib.sha256(data).hexdigest() for name,data in payload.items()},
            'unrelated_entries_preserved':len(before)-int(page in before),'runtime_verified':False,'trx_verified':False}

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('romfs',type=Path);parser.add_argument('metadata',type=Path)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    if args.report.exists():raise SystemExit('Report exists')
    result=stage(args.romfs,json.loads(args.metadata.read_text()))
    args.report.write_text(json.dumps(result,indent=2)+'\n')
