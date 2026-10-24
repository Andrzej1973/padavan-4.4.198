#!/usr/bin/env python3
"""Stage resumable software close beside legacy close; not production binding."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();root=a.source.resolve();out=a.output.resolve()
if out.exists() or out==root or root in out.parents or out in root.parents:raise SystemExit('New separate output required')
name='common/rtmp_init_inf.c';data=(root/name).read_bytes()
if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!='232b6c3d68224e896aaf9364aad871b787bdc578':raise SystemExit('Unreviewed close source')
s=data.decode();sig='VOID RTMPDrvClose(VOID *pAdSrc, VOID *net_dev)';start=s.index(sig);end=s.index('\n}',start)+2;f=s[start:end]
anchor='\t/* Close kernel threads*/\n\tRtmpMgmtTaskExit(pAd);'
if f.count(anchor)!=1:raise SystemExit('Changed join boundary')
body=f[f.index('\n{')+2:-2]
decl='\n\tRTMP_ADAPTER *pAd = (RTMP_ADAPTER *)pAdSrc;\n\tUINT32 i = 0;'
if not body.startswith(decl):raise SystemExit('Changed close declarations')
pre,post=body[len(decl):].split(anchor)
if 'return;' in pre+post:raise SystemExit('Unreviewed early return in close')
# Once radio-off reports failure, do not free IRQ/rings or pretend completed.
# Stage 3 is retained uncertainty, not a retryable stage or hardware recovery.
radio_failure='\t\t\tif (brc==FALSE)\n\t\t\t{'
if post.count(radio_failure)!=1:raise SystemExit('Changed radio-off failure branch')
failure_end=post.index('\n\t\t\t}',post.index(radio_failure))
post=post[:failure_end]+'\n\t\t\t\tRTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);\n\t\t\t\tpAd->wr_iot_transition.shutdown_stage=3U;\n\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);\n\t\t\t\treturn NDIS_STATUS_FAILURE;'+post[failure_end:]
checked='''INT wr_iot_drv_close_checked(VOID *pAdSrc, VOID *net_dev,
 const struct wr_iot_radio_ticket *ticket)
{
 RTMP_ADAPTER *pAd = (RTMP_ADAPTER *)pAdSrc;
 UINT32 i = 0;
 ULONG flags;
 unsigned int stage;
 (void)net_dev; /* Some compile configurations have no IRQ-release use. */
 if (!pAd || !ticket) return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 if (ticket->operation != WR_RADIO_CLOSE || pAd->wr_iot_transition.busy != WR_RADIO_CLOSE ||
     ticket->serial != pAd->wr_iot_transition.serial) {
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
  return NDIS_STATUS_FAILURE;
 }
 stage=pAd->wr_iot_transition.shutdown_stage;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 if (stage > 2U) return NDIS_STATUS_FAILURE;
 if (stage == 2U) return NDIS_STATUS_SUCCESS;
 if (stage == 0U) {
'''+pre+'''
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
  pAd->wr_iot_transition.shutdown_stage=1U;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 }
 if (wr_iot_mgmt_exit_checked(pAd,ticket) != NDIS_STATUS_SUCCESS)
  return NDIS_STATUS_FAILURE;
'''+post+'''
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 pAd->wr_iot_transition.shutdown_stage=2U;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 return NDIS_STATUS_SUCCESS;
}
'''
s=s[:end]+'\n\n'+checked+s[end:]
if (root/name).read_bytes()!=data:raise SystemExit('Source changed')
(out/'common').mkdir(parents=True);(out/name).write_text(s,encoding='utf-8')
(out/'manifest.json').write_text(json.dumps({'production_installed':False,'checked_close_staged':True,'legacy_callers_replaced':False,'prejoin_resource_safety_proven':False,'outer_retention_proven':False,'hardware_close_verified':False,'target_compiled':False},indent=2)+'\n')
print('Staged resumable software close; legacy/outer lifetime and prejoin safety pending')
