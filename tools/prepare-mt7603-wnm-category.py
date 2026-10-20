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


def transform(text):
    if text.count(NEW) == 1:
        return text
    if text.count(OLD) != 1:
        raise ValueError('Expected one CATEGORY_WNM incorrectly guarded by PMF')
    return text.replace(OLD, NEW, 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    path = args.source / 'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/include/rtmp_def.h'
    text = transform(path.read_text(encoding='utf-8'))
    if text.count(NEW) != 1:
        raise ValueError('WNM action category is not scoped to 802.11v support')
    path.write_bytes(text.encode('utf-8'))
    print('Prepared MT7603 WNM category guard independently of PMF')
