#!/usr/bin/env python3
"""Correct diagnostic percentage arithmetic in the pinned MT7603 SDK source."""
import argparse
from pathlib import Path


def compose(source):
    counter = 'pAd->WlanCounters.'
    formulas = [
        ('txCount', counter + 'FailedCount.u.LowPart', 'txCount', 1000),
        ('txCount', counter + 'RetryCount.u.LowPart+' + counter + 'FailedCount.u.LowPart', 'txCount', 1000),
        ('txCount', counter + 'FailedCount.u.LowPart', 'txCount', 10000),
        ('rxCount', counter + 'FCSErrorCount.u.LowPart', 'rxCount', 1000),
        (counter + 'ReceivedFragmentCount.u.LowPart', counter + 'FCSErrorCount.u.LowPart',
         counter + 'ReceivedFragmentCount.u.LowPart', 1000),
        ('mpduTXCount', counter + 'AmpduFailCount.u.LowPart', 'mpduTXCount', 1000),
    ]
    for guard, failures, successes, scale in formulas:
        # Preserve the original failure predicate for each reviewed formula.
        numerator = failures if scale == 10000 else '(' + failures + ')'
        old = f'{guard}==0? 0: {scale}*{numerator}/({failures}+{successes})'
        if source.count(old) != 1:
            raise ValueError('Statistics formula changed: ' + old)
        wide = failures.replace('+', '+(u64)')
        new = f'wr_wifi_stats_ratio((u64){wide}, (u64){successes}, {scale})'
        source = source.replace(old, new, 1)
    old = ('ampdu_fail_cnt = pAd->RalinkCounters.OneSecTxAMpduCnt - pAd->RalinkCounters.OneSecTxBACnt;\n'
           '\t\t\tampdu_fail_ratio = (ampdu_fail_cnt * 100) / pAd->RalinkCounters.OneSecTxAMpduCnt;')
    new = ('ampdu_fail_cnt = pAd->RalinkCounters.OneSecTxAMpduCnt >= pAd->RalinkCounters.OneSecTxBACnt ?\n'
           '\t\t\t pAd->RalinkCounters.OneSecTxAMpduCnt - pAd->RalinkCounters.OneSecTxBACnt : 0;\n'
           '\t\t\tampdu_fail_ratio = wr_wifi_stats_ratio((u64)ampdu_fail_cnt,\n'
           '\t\t\t (u64)pAd->RalinkCounters.OneSecTxAMpduCnt - ampdu_fail_cnt, 100);')
    if source.count(old) != 1:
        raise ValueError('No-BA statistics anchor changed')
    source = source.replace(old, new, 1)
    anchor = '#include "rt_config.h"'
    if source.count(anchor) != 1:
        raise ValueError('Statistics include anchor changed')
    return source.replace(anchor, anchor + '\n#include "wr-wifi-stats-ratio.h"', 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver', type=Path)
    args = parser.parse_args()
    path = args.driver / 'ap/ap_cfg.c'
    header = args.driver / 'include/wr-wifi-stats-ratio.h'
    if header.exists():
        parser.error('Statistics helper already exists')
    changed = compose(path.read_text())
    header.write_bytes(Path(__file__).with_name('wifi-stats-ratio.h').read_bytes())
    path.write_text(changed)
    print('Prepared diagnostic percentage arithmetic; target/runtime verification pending')
