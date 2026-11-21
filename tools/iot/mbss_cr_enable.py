"""Check the MT MBSS CR_ENABLE result without dropping a claimed vendor ref."""


def guard_cr_enable(raw: str) -> str:
    anchor = (
        '    RTMP_AP_IoctlHandle(pAd, NULL, '
        'CMD_RTPRIV_IOCTL_MBSS_CR_ENABLE, 0, pDev, 0);'
    )
    if raw.count(anchor) != 1:
        raise ValueError('Changed MBSS CR_ENABLE return anchor')
    return raw.replace(
        anchor,
        '    if (RTMP_AP_IoctlHandle(pAd, NULL, '
        'CMD_RTPRIV_IOCTL_MBSS_CR_ENABLE, 0, pDev, 0)\n'
        '        != NDIS_STATUS_SUCCESS) {\n'
        '        /* Virtual UP already claimed a vendor reference. A failed CR_ENABLE\n'
        '         * may have changed hardware: retain the module pin for recovery. */\n'
        '        return -3; /* vendor UP was acquired; close needs an owner */\n'
        '    }',
        1,
    )
