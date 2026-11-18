"""Make vendor group-key peer-address packing defined for bytes >= 0x80.

Only integer promotion changes; no register address, ownership or queue change.
"""


def compose(text):
    old = 'dw1->word = CmdKey.aucPeerAddr[0] + (CmdKey.aucPeerAddr[1] << 8) +(CmdKey.aucPeerAddr[2] << 16) +(CmdKey.aucPeerAddr[3] << 24);'
    new = 'dw1->word = (UINT32)CmdKey.aucPeerAddr[0] | ((UINT32)CmdKey.aucPeerAddr[1] << 8) | ((UINT32)CmdKey.aucPeerAddr[2] << 16) | ((UINT32)CmdKey.aucPeerAddr[3] << 24);'
    if text.count(old) != 2 or new in text:
        raise ValueError('Expected exactly two native group-key peer packing sites')
    return text.replace(old, new)
