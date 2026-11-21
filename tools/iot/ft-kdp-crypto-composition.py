"""Prepare checked KDP crypto + ioctl refusal propagation; uninstalled.

Cache lifetime must cover all KDP users and release before this can be enabled.
This holds allocation lifetime only; CryptKey writer serialization remains open.
"""

def compose(source,ioctl):
    if 'wr_ft_kdp_encrypt_checked(' in source or 'wr_ft_kdp_encrypt_checked(' in ioctl:
        raise ValueError('KDP crypto already composed')
    code=[]
    for operation in ('Encrypt','Decrypt'):
        signature='VOID TYPE_FUNC FT_KDP_Data'+operation+'('
        if source.count(signature)!=1:raise ValueError('KDP crypto definition changed')
        start=source.index(signature);end=source.index('\n}',start)+2
        native=source[start:end]
        native=native.replace(signature,'static BOOLEAN wr_native_kdp_'+operation+'(',1)
        native=native.replace('return;','return FALSE;')
        native=native.replace('{\n#ifndef FT_KDP_EMPTY','{\n (void)pAd;(void)pData;(void)pDataLen;\n#ifndef FT_KDP_EMPTY',1)
        anchor='\t*pDataLen = OutputLen;'
        if native.count(anchor)!=1:raise ValueError('KDP output assignment changed')
        capacity='*pDataLen + FT_KDP_KEY_ENCRYPTION_EXTEND' if operation=='Encrypt' else '*pDataLen'
        native=native.replace(anchor,' if(!OutputLen||OutputLen>'+capacity+'){'
            'FT_MEM_FREE(pAd,pOutputBuf);return FALSE;}\n'+anchor,1)
        anchor='\tFT_MEM_FREE(pAd, pOutputBuf);\n#endif /* FT_KDP_EMPTY */'
        if native.count(anchor)!=1:raise ValueError('KDP crypto cleanup changed')
        native=native.replace(anchor,'\tFT_MEM_FREE(pAd, pOutputBuf);\n return TRUE;\n#endif /* FT_KDP_EMPTY */\n return FALSE;',1)
        native=native.replace('UCHAR *pOutputBuf;',
            'UCHAR *pOutputBuf; UCHAR wr_key[16]; unsigned int wr_key_i;',1)
        aes='AES_Key_Wrap(' if operation=='Encrypt' else 'AES_Key_Unwrap('
        if native.count(aes)!=1 or native.count('FT_KDP_CB->CryptKey')!=1:
            raise ValueError('native crypto key read changed')
        native=native.replace(aes,
            'RTMP_SEM_LOCK(&pAd->ApCfg.FtTab.FT_KdpLock);\n'
            ' NdisMoveMemory(wr_key,FT_KDP_CB->CryptKey,sizeof(wr_key));\n'
            ' RTMP_SEM_UNLOCK(&pAd->ApCfg.FtTab.FT_KdpLock);\n '+aes,1)
        # Only the AES argument uses the owned snapshot; the locked copy still
        # reads the actual native key. Clear immediately after synchronous AES.
        native=native.replace('FT_KDP_CB->CryptKey, 16,','wr_key, 16,',1)
        assignment=' if(!OutputLen||OutputLen>'
        native=native.replace(assignment,
            ' for(wr_key_i=0;wr_key_i<sizeof(wr_key);wr_key_i++)'
            '((volatile UCHAR *)wr_key)[wr_key_i]=0;\n'+assignment,1)
        public='wr_ft_kdp_'+operation.lower()+'_checked'
        wrapper='''
BOOLEAN NAME(RTMP_ADAPTER *pAd,UCHAR *data,UINT32 *length)
{
 struct wr_ft_cache_lease lease={0};BOOLEAN admitted,result;
 if(!pAd||!data||!length||!*length||*length>~0U-8U||
    !pAd->wr_ft_cache_lifetime_initialized)return FALSE;
 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 admitted=wr_ft_cache_enter(&pAd->wr_ft_cache_lifetime,&lease);
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
 if(!admitted)return FALSE;
 result=FALSE;
 if(pAd->ApCfg.FtTab.FlgIsFtKdpInit==1&&pAd->ApCfg.FtTab.pFT_KDP_Ctrl_BK)
  result=wr_native_kdp_OP(pAd,data,length);
 RTMP_SEM_LOCK(&pAd->wr_ft_cache_lifetime_lock);
 if(!wr_ft_cache_leave(&pAd->wr_ft_cache_lifetime,&lease))result=FALSE;
 RTMP_SEM_UNLOCK(&pAd->wr_ft_cache_lifetime_lock);
 return result;
}
'''.replace('NAME',public).replace('OP',operation)
        code.append(native+'\n'+wrapper)
        call='FT_KDP_Data'+operation+'(pAd, (UCHAR *)pBuffer, &DataLen);'
        if ioctl.count(call)!=1:raise ValueError('KDP ioctl call changed')
        ioctl=ioctl.replace(call,'if(!(wr_crypto_ok='+public+'(pAd,(UCHAR *)pBuffer,&DataLen))){\n'
            ' Status=-EAGAIN;wrq->u.data.length=0;break;\n}',1)
    declaration='UINT32 DataLen;'
    copy='wrq->u.data.length = DataLen;'
    if ioctl.count(declaration)!=1 or ioctl.count(copy)!=1:
        raise ValueError('ioctl shared cleanup anchors changed')
    ioctl=ioctl.replace(declaration,declaration+'\n BOOLEAN wr_crypto_ok=FALSE;',1)
    ioctl=ioctl.replace(copy,'if(!wr_crypto_ok){FT_MEM_FREE(pAd,pBuffer);break;}\n '+copy,1)
    return '\n'.join(code),ioctl
