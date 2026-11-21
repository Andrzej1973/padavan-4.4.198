"""Prepare trusted-payload native key functions; not installed by producer yet.

Input must already contain the reviewed failed-copy rejection. Native key body
bytes are preserved; this factoring alone supplies no association lifetime pin.
"""
def compose(text):
    if 'wr_iot_hostapd_set_key_native' in text:
        raise ValueError('HOSTAPD execution factoring already present')
    changes=[];receipts=[]
    # Limit each extraction to its exact native switch branch.
    for case,next_case,payload,kind,body_start in (
        ('HOSTAPD_OID_SET_KEY','HOSTAPD_OID_DEL_KEY','Key','set',
         'if((Key.ik_type == CIPHER_WEP64)'),
        ('HOSTAPD_OID_DEL_KEY','HOSTAPD_OID_SET_STA_AUTHORIZED','delkey','del',
         'if (pEntry){')):
        start=text.index('case '+case+':')
        end=text.index('case '+next_case+':',start)
        region=text[start:end]
        if region.count('if (Status) { Status = -EFAULT; break; }')!=1:
            raise ValueError('trusted payload copy precondition missing: '+case)
        begin=region.index(body_start)
        # Keep whitespace before the final switch break at the original site.
        finish=region.rindex('break;')
        while finish>begin and region[finish-1] in ' \t':finish-=1
        body=region[begin:finish]
        if 'break;' in body or 'return ' in body or 'copy_from_user' in body:
            raise ValueError('native key body control-flow changed: '+case)
        # SET's switch case has an outer brace, excluded with the final break.
        typ='ieee80211req_key' if kind=='set' else 'ieee80211req_del_key'
        selector='apidx' if kind=='set' else 'pObj->ioctl_if'
        call='Status = wr_iot_hostapd_'+kind+'_key_native(pAd,'+selector+',pEntry,'+payload+');\n'
        changes.append((body,call,kind,typ,payload))
        replacement=region[:begin]+call+region[finish:]
        if kind=='set':
            declaration='\t\t\tUINT KeyIdx;\n'
            if replacement.count(declaration)!=1:raise ValueError('SET local declaration changed')
            replacement=replacement.replace(declaration,'',1)
        receipts.append((region,replacement))
        text=text[:start]+replacement+text[end:]
    helpers='\n#ifdef HOSTAPD_SUPPORT\n'
    for body,call,kind,typ,payload in changes:
        declarations='\n UINT KeyIdx;UINT8 Wcid;BSS_STRUCT *pMbss;' if kind=='set' else '\n (void)apidx;'
        helpers+=('static INT wr_iot_hostapd_'+kind+'_key_native(RTMP_ADAPTER *pAd,\n'
          ' UINT apidx,MAC_TABLE_ENTRY *pEntry,struct '+typ+' '+payload+')\n{'+
          declarations+'\n'+body+'\n return NDIS_STATUS_SUCCESS;\n}\n')
    helpers+='#endif\n'
    signature='INT RTMPAPSetInformation('
    if text.count(signature)!=1:raise ValueError('native ioctl definition changed')
    text=text.replace(signature,helpers+'\n'+signature,1)
    return text,helpers,receipts
