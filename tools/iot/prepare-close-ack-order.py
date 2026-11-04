#!/usr/bin/env python3
"""Prepare staged MT7603 close overlay. Integration remains target-unverified."""
import argparse
import hashlib
import importlib.util
import json
import re
from pathlib import Path


def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def prepare(files):
    result=dict(files)
    def one(name,old,new):
        if result[name].count(old)!=1:raise ValueError('Changed close-order anchor: '+name+': '+old)
        result[name]=result[name].replace(old,new)
    def body(text,signature):
        start=text.index(signature);end=text.index('\n}',start)+2
        return start,end,text[start:end]
    ap='ap/ap.c';asic='hw_ctrl/cmm_asic_mt.c';close='common/rtmp_init_inf.c'
    result[ap]=load('prepare-ap-resource-split').split(result[ap])
    one(ap,' * Unbound candidate: no radio/IRQ/DMA completion or retry proof is implied. */',
        ' * Isolated checked-close binding only; hardware/runtime acceptance remains open. */')
    lane_names=('include/rtmp.h','common/rtmp_init.c','include/wr-iot-nettask-schedule.inc',
                'os/linux/rt_rbus_pci_drv.c')
    result.update(load('prepare-nettask-data-lane').prepare({n:result[n] for n in lane_names}))
    # Reuse the exact checked queue/MAC RX stop prefix; no IRQ/DMA shutdown.
    start,end,off=body(result[asic],'BOOLEAN wr_iot_mt_radio_off_checked(')
    if off.count('wr_iot_send_radio_off_checked(pAd,ticket)')!=1:
        raise ValueError('Expected ticket-owned OFF transport')
    first=off.index(' if (stage == 0U) {');last=off.index(' if (stage == 1U) {',first)
    prefix=off[:last].replace('BOOLEAN wr_iot_mt_radio_off_checked(',
                            'BOOLEAN wr_iot_mt_prepare_close_rx(',1)
    prefix=prefix.replace(' WPDMA_GLO_CFG_STRUC cfg;\n','',1)
    prefix=prefix.replace(' UINT32 arb, rqcr, tqcr0;',' UINT32 arb, rqcr;',1)
    prefix+=' return TRUE;\n}\n'
    off=off[:first]+(' if (stage == 0U) {\n'
        '  if (!wr_iot_mt_prepare_close_rx(pAd,ticket)) return FALSE;\n'
        '  stage=1U;\n }\n')+off[last:]
    if off.count(' INT32 bss;\n')!=1:raise ValueError('Changed BSS iteration declaration')
    off=off.replace(' INT32 bss;\n','',1)
    result[asic]=result[asic][:start]+prefix+'\n'+off+result[asic][end:]
    one('include/rtmp.h','BOOLEAN wr_iot_mt_radio_off_checked(',
        'BOOLEAN wr_iot_mt_prepare_close_rx(RTMP_ADAPTER *pAd, const struct wr_iot_radio_ticket *ticket);\n'
        'BOOLEAN wr_iot_mt_radio_off_checked(')
    one('include/radio-transition.h','unsigned long serial,retired_serial,epoch;',
        'unsigned long serial,retired_serial,epoch,ap_cleanup_serial;')
    one('include/radio-transition.h','s->serial=0;s->retired_serial=0;',
        's->serial=0;s->retired_serial=0;s->ap_cleanup_serial=0;')
    # All irreversible AP/resource cleanup happens only after global joins.
    helper=Path(__file__).with_name('ap-release-after-join.inc').read_text()
    result[ap]+='\n'+helper
    one('include/ap.h','BOOLEAN wr_iot_ap_shutdown_before_radio_off(RTMP_ADAPTER *pAd);',
        'BOOLEAN wr_iot_ap_shutdown_before_radio_off(RTMP_ADAPTER *pAd);\nstruct wr_iot_radio_ticket;\n'
        'BOOLEAN wr_iot_ap_release_after_join(RTMP_ADAPTER *pAd,const struct wr_iot_radio_ticket *ticket);')
    start,end,f=body(result[close],'static INT wr_iot_checked_close_body(')
    def change(old,new):
        nonlocal f
        if f.count(old)!=1:raise ValueError('Changed checked close block: '+old)
        f=f.replace(old,new)
    mt='(IS_MT7603(pAd) && pAd->chipCap.hif_type == HIF_MT)'
    change(' if (stage == 0U) {',' if (stage == 0U) {\n'
        '#if defined(MT_MAC) && defined(RTMP_MAC_PCI) && defined(RTMP_PCI_SUPPORT)\n'
        '  if '+mt+' {\n'
        '   if (!wr_iot_mt_prepare_close_rx(pAd,ticket) ||\n'
        '       wr_iot_nettask_data_exit(pAd)!=NDIS_STATUS_SUCCESS)\n'
        '    return NDIS_STATUS_FAILURE;\n  }\n#endif')
    change('if (!APShutdown(pAd)) {','if (!('+mt+' ? wr_iot_ap_shutdown_before_radio_off(pAd) : APShutdown(pAd))) {')
    # Data callbacks were joined above; MCU RX1 must not be joined here.
    change('if (RtmpNetTaskExit(pAd) != NDIS_STATUS_SUCCESS) {',
           'if (!'+mt+' && RtmpNetTaskExit(pAd) != NDIS_STATUS_SUCCESS) {')
    for call in ('RTMPDisableRxTx(pAd);','DISABLE_TX_RX(pAd, RTMP_HALT);',
                 'RTMP_ASIC_INTERRUPT_DISABLE(pAd);','MeasureReqTabExit(pAd);','TpcReqTabExit(pAd);',
                 'AutoChBssTableDestroy(pAd);','ChannelInfoDestroy(pAd);'):
        f,count=re.subn(r'(?m)^([ \t]*)'+re.escape(call)+r'[ \t]*$',
                        lambda m:m.group(1)+'if (!'+mt+') '+call,f)
        if count!=1:raise ValueError('Changed active close call: '+call)
    anchor='\t/* Free IRQ*/'
    change(anchor,' if '+mt+' {\n'
        '  if (RtmpNetTaskExit(pAd)!=NDIS_STATUS_SUCCESS)return NDIS_STATUS_FAILURE;\n'
        ' }\n'+anchor)
    anchor='#ifdef SINGLE_SKU_V2'
    change(anchor,' if '+mt+' {\n'
        '  /* From this point a partial failure must retain, never replay frees. */\n'
        '  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);\n'
        '  pAd->wr_iot_transition.shutdown_stage=6U;\n'
        '  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);\n'
        '#ifdef CONFIG_AP_SUPPORT\n'
        '  if (!wr_iot_ap_release_after_join(pAd,ticket))return NDIS_STATUS_FAILURE;\n'
        '#endif\n }\n'+anchor)
    result[close]=result[close][:start]+f+result[close][end:]
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('output',type=Path,nargs='?')
    p.add_argument('--install-isolated',action='store_true');a=p.parse_args()
    src=a.source.resolve()
    manifest=None;manifest_path=src.with_name(src.name+'.manifest.json')
    if a.install_isolated:
        if a.output is not None:p.error('No overlay output with isolated installation')
        raw_manifest=manifest_path.read_bytes();manifest=json.loads(raw_manifest)
        actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest()
                for f in src.rglob('*') if f.is_file()}
        if (manifest.get('production_installed') is not False or
            manifest.get('target_compiled') is not False or
            'mcu_owned_off' not in manifest or actual!=manifest['merged_driver_sha256']):
            p.error('Expected unchanged isolated owned-OFF candidate')
        out=src
    else:
        if a.output is None:p.error('Overlay output required')
        out=a.output.resolve()
        if out.exists() or src==out or src in out.parents or out in src.parents:
            p.error('Expected new separate overlay')
    names=('ap/ap.c','include/ap.h','include/rtmp.h','include/radio-transition.h',
           'hw_ctrl/cmm_asic_mt.c','common/rtmp_init.c','common/rtmp_init_inf.c',
           'include/wr-iot-nettask-schedule.inc','os/linux/rt_rbus_pci_drv.c')
    changes=prepare({n:(src/n).read_text() for n in names})
    if not a.install_isolated:out.mkdir(parents=True)
    for n,text in changes.items():
        path=out/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
    hashes={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in changes}
    report={
        'scope':'staged close source overlay; not installed',
        'output_sha256':hashes,'target_compiled':False,'runtime_verified':False}
    if manifest is not None:
        manifest['merged_driver_sha256'].update(hashes)
        manifest['candidate_driver_sha256'].update(hashes)
        report.update(scope='isolated checked-close binding only',ordinary_callbacks_bound=False,
                      input_manifest_sha256=hashlib.sha256(raw_manifest).hexdigest(),
                      firmware_epoch_verified=False,terminal_partial_cleanup_stage=6)
        manifest['close_ack_order']=report
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    else:(out/'overlay.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
