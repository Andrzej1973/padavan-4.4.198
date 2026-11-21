"""Reject failed HOSTAPD key payload copies before native lookup/mutation.

A local input-admission correction, not BSS/generation lifetime arbitration.
"""
def compose(text):
    result=text
    for payload in ('Key','delkey'):
        old='Status = copy_from_user(&'+payload+', wrq->u.data.pointer, wrq->u.data.length);'
        new=old+'\n\t\t\tif (Status) { Status = -EFAULT; break; }'
        if result.count(old)!=1 or new in result:
            raise ValueError('HOSTAPD key copy anchor changed/already installed: '+payload)
        result=result.replace(old,new,1)
    return result
