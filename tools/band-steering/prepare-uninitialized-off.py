#!/usr/bin/env python3
"""Confirm actual OFF without initializing disabled candidate tables."""
import sys
from pathlib import Path
root = Path(sys.argv[1])/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'
legacy = root/'mt76x2/ap/ap_band_steering.c'
modern = root/'mt76x3/ap/ap_band_steering.c'
texts = [legacy.read_text(), modern.read_text()]
old_legacy = '\tif (table->bInitialized == FALSE)\n\t\treturn BND_STRG_NOT_INITIALIZED;\n\t\r\n'
# Match inside the IOCTL entry only; several other functions use this guard.
start = texts[0].index('INT BndStrg_MsgHandle(')
end = texts[0].index('\n}', start)+2
body = texts[0][start:end]
anchor = '\tif (table->bInitialized == FALSE)\n\t\treturn BND_STRG_NOT_INITIALIZED;'
if body.count(anchor) != 1:
    raise SystemExit('Legacy uninitialized guard changed; no files written')
replacement = '''	if (table->bInitialized == FALSE) {
		BNDSTRG_MSG request = { 0 }, response = { 0 };
		if (wrq->u.data.length != sizeof(request) ||
			copy_from_user(&request, wrq->u.data.pointer, sizeof(request)))
			return BND_STRG_INVALID_ARG;
		if (request.Action != BNDSTRG_ONOFF || request.OnOff || table->bEnabled ||
			!pAd->net_dev || ((POS_COOKIE)pAd->OS_Cookie)->ioctl_if != 0)
			return BND_STRG_NOT_INITIALIZED;
		response.Action = BNDSTRG_ONOFF;
		RtmpOSWrielessEventSend(pAd->net_dev, RT_WLAN_EVENT_CUSTOM,
			OID_BNDSTRG_MSG, NULL, (UCHAR *)&response, sizeof(response));
		return BND_STRG_SUCCESS;
	}'''
new_legacy = texts[0][:start]+body.replace(anchor,replacement)+texts[0][end:]
start = texts[1].index('INT BndStrg_MsgHandle(')
end = texts[1].index('\n}', start)+2
body = texts[1][start:end]
anchor = '\tif (!table || (table->bInitialized == FALSE)) {\n'
if body.count(anchor) != 1:
    raise SystemExit('Modern uninitialized guard changed; no files written')
replacement = anchor+'''		BNDSTRG_MSG request = { 0 }, response = { 0 };
		INT index;
		if (wrq->u.data.length != sizeof(request) ||
			copy_from_user(&request, wrq->u.data.pointer, sizeof(request)))
			return BND_STRG_INVALID_ARG;
		if (apidx != 0 || !pAd->net_dev || request.Action != BNDSTRG_ONOFF ||
			request.data.onoff.OnOff)
			return BND_STRG_NOT_INITIALIZED;
		for (index = 0; index < DBDC_BAND_NUM; ++index) {
			PBND_STRG_CLI_TABLE candidate = P_BND_STRG_TABLE(index);
			if (candidate->bEnabled || (candidate->bInitialized &&
				candidate->DaemonPid != 0xffffffff && candidate->DaemonPid != current->pid))
				return BND_STRG_NOT_INITIALIZED;
		}
		response.Action = BNDSTRG_ONOFF;
		response.data.onoff.Band = WMODE_CAP_5G(pAd->ApCfg.MBSSID[0].wdev.PhyMode) ? BAND_5G : BAND_24G;
		memcpy(response.data.onoff.ucIfName, pAd->net_dev->name, sizeof(response.data.onoff.ucIfName));
		RtmpOSWrielessEventSend(pAd->net_dev, RT_WLAN_EVENT_CUSTOM,
			OID_BNDSTRG_MSG, NULL, (UCHAR *)&response, sizeof(response));
		return BND_STRG_SUCCESS;
'''
# The original warning/return remain after the explicit handled return.
new_modern = texts[1][:start]+body.replace(anchor,replacement)+texts[1][end:]
legacy.write_text(new_legacy)
modern.write_text(new_modern)
print('OFF-only uninitialized readback added; no table initialization, enables or owner takeover')
