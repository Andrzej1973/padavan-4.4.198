#!/usr/bin/env python3
"""Guard the 802.11v category constant by WNM, not unrelated PMF support."""
import argparse
from pathlib import Path

OLD = '''#ifdef DOT11W_PMF_SUPPORT
#define CATEGORY_SA\t\t\t8\t/* defined in IEEE 802.11w-D8.0 7.3.1.11*/
#define CATEGORY_PD\t\t\t9\t/* Protected Dual of Action defined in IEEE 802.11w */
#define CATEGORY_WNM 10
#define CATEGORY_VSP\t\t\t126\t/* Vendor-specific Protected defined in IEEE 802.11w */
#endif // DOT11W_PMF_SUPPORT //'''
NEW = '''#ifdef DOT11W_PMF_SUPPORT
#define CATEGORY_SA\t\t\t8\t/* defined in IEEE 802.11w-D8.0 7.3.1.11*/
#define CATEGORY_PD\t\t\t9\t/* Protected Dual of Action defined in IEEE 802.11w */
#define CATEGORY_VSP\t\t\t126\t/* Vendor-specific Protected defined in IEEE 802.11w */
#endif // DOT11W_PMF_SUPPORT //

#ifdef CONFIG_DOT11V_WNM
#define CATEGORY_WNM 10
#endif'''

TLV_START = 'VOID FT_FTIE_InsertIGTKSubIE('
TLV_END = 'VOID FT_InsertTimeoutIntervalIE('


def transform(text):
    if text.count(NEW) == 1:
        return text
    if text.count(OLD) != 1:
        raise ValueError('Expected one CATEGORY_WNM incorrectly guarded by PMF')
    return text.replace(OLD, NEW, 1)


def transform_tlv(text):
    start = text.find(TLV_START)
    end = text.find(TLV_END, start + len(TLV_START)) if start >= 0 else -1
    if start >= 0 and text[:start].endswith('#ifdef DOT11W_PMF_SUPPORT\n'):
        return text
    if start < 0 or end < 0:
        raise ValueError('Expected the IGTK FT helper before FT_InsertTimeoutIntervalIE')

    function = text[start:end]
    close = function.rfind('}')
    if close < 0 or function[close + 1:].strip():
        raise ValueError('Could not isolate the IGTK FT helper body')
    wrapped = '#ifdef DOT11W_PMF_SUPPORT\n' + function[:close + 1] + '\n#endif /* DOT11W_PMF_SUPPORT */\n\n'
    return text[:start] + wrapped + text[end:]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    driver = args.source / 'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3'
    path = driver / 'include/rtmp_def.h'
    text = transform(path.read_text(encoding='utf-8'))
    if text.count(NEW) != 1:
        raise ValueError('WNM action category is not scoped to 802.11v support')
    path.write_bytes(text.encode('utf-8'))

    path = driver / 'common/ft_tlv.c'
    text = transform_tlv(path.read_text(encoding='utf-8'))
    if text.count('#ifdef DOT11W_PMF_SUPPORT\n' + TLV_START) != 1:
        raise ValueError('FT IGTK helper is not scoped to PMF support')
    path.write_bytes(text.encode('utf-8'))
    print('Prepared MT7603 WNM and PMF feature guards')
