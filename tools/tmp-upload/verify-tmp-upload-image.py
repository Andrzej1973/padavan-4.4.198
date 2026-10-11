#!/usr/bin/env python3
"""Verify staged tmpfs action and translations; no router runtime claim."""
import argparse
from pathlib import Path

def verify(romfs):
    web = romfs / 'www'
    action = (web / 'bit_action.asp').read_text(encoding='utf-8')
    upgrade = (web / 'Advanced_FirmwareUpgrade_Content.asp').read_text(encoding='utf-8')
    binary = (romfs / 'usr/sbin/httpd').read_bytes()
    if b'window.wrTmpResult=%d;window.wrTmpLimit=%llu;' not in binary:
        raise ValueError('Missing linked tmpfs action result in httpd')
    if b'mount -t tmpfs -o remount,rw,size=50M tmpfs /tmp' in binary:
        raise ValueError('Unchecked legacy tmpfs command remains in httpd')
    if "submitInternet('bigtmp');" not in upgrade or '<#TMP_btn#>' not in upgrade:
        raise ValueError('Missing firmware upload button/action')
    if 'style="width:50px display:none;"' in upgrade:
        raise ValueError('Legacy button width remains')
    for key in ('TMP_result_ok', 'TMP_result_memory', 'TMP_result_failed'):
        if '<#' + key + '#>' not in action:
            raise ValueError('Missing response label: ' + key)
    if 'alert(text' not in action or 'setTimeout(' not in action or action.index('alert(text') > action.index('setTimeout('):
        raise ValueError('Result feedback must precede redirect')
    for language in ('EN', 'UK', 'RU'):
        lines = (web / (language + '.dict')).read_text(encoding='utf-8').splitlines()
        for key in ('TMP_btn', 'FW_desc7', 'TMP_result_ok', 'TMP_result_memory', 'TMP_result_failed'):
            values = [line.split('=', 1)[1] for line in lines if line.startswith(key + '=')]
            if len(values) != 1 or not values[0].strip():
                raise ValueError(language + ': missing or duplicate label ' + key)
    return 'PASS: staged upload button, linked result and EN/UK/RU labels; runtime unverified'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('romfs', type=Path)
    print(verify(parser.parse_args().romfs))
