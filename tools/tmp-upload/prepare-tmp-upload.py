#!/usr/bin/env python3
"""Prepare guarded /tmp upload action with EN/UK/RU feedback."""
import argparse
from pathlib import Path
import shutil
import re

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Expected exactly one source anchor: ' + old[:60])
    return text.replace(old, new, 1)

def prepare(root):
    http = root / 'trunk/user/httpd'
    web = root / 'trunk/user/www/n56u_ribbon_fixed'
    source = http / 'web_ex.c'
    page = web / 'bit_action.asp'
    upgrade = web / 'Advanced_FirmwareUpgrade_Content.asp'
    original = source.read_text(encoding='utf-8')
    old = '\t\tsystem("mount -t tmpfs -o remount,rw,size=50M tmpfs /tmp");'
    new = '''\t\tunsigned long long limit_mib = 0;
\t\tint result = -5;
\t\tif (get_login_safe()) result = wr_tmp_upload_increase(&limit_mib);
\t\twebsWrite(wp, "<script>window.wrTmpResult=%d;window.wrTmpLimit=%llu;</script>\\n", result, limit_mib);'''
    modified = replace_once(original, old, new)
    modified = replace_once(modified, 'static int update_action_hook(', '#include "tmp-upload-guard.h"\n\nstatic int update_action_hook(')
    response = page.read_text(encoding='utf-8')
    response = replace_once(response, 'function Callback(){', '''function Callback(){
    if (typeof window.wrTmpResult === 'number') {
        var text = window.wrTmpResult > 0 ? '<#TMP_result_ok#>' :
            (window.wrTmpResult === -2 ? '<#TMP_result_memory#>' : '<#TMP_result_failed#>');
        alert(text + ' ' + window.wrTmpLimit + ' MiB');
    }''')
    upgrade_content = replace_once(upgrade.read_text(encoding='utf-8'),
        'style="width:50px display:none;"', 'style="margin-left:8px;"')
    labels = {
        'EN.footer': ('Increase /tmp', 'Temporarily increase the /tmp upload limit if memory permits. This does not add RAM.', 'Available /tmp limit:', 'Insufficient free memory. Unchanged /tmp limit:', 'Could not verify an increased /tmp limit. Reported limit:'),
        'UK.dict': ('Збільшити /tmp', 'Тимчасово збільшити ліміт /tmp для завантаження прошивки, якщо вистачає пам’яті. Це не додає RAM.', 'Доступний ліміт /tmp:', 'Недостатньо вільної пам’яті. Ліміт /tmp не змінено:', 'Не вдалося підтвердити збільшення /tmp. Отриманий ліміт:'),
        'RU.dict': ('Увеличить /tmp', 'Временно увеличить лимит /tmp для загрузки прошивки, если хватает памяти. Это не добавляет RAM.', 'Доступный лимит /tmp:', 'Недостаточно свободной памяти. Лимит /tmp не изменён:', 'Не удалось подтвердить увеличение /tmp. Полученный лимит:'),
    }
    dictionaries = []
    for name, values in labels.items():
        path = root / 'trunk/user/www/dict' / name
        content = path.read_text(encoding='utf-8')
        for key, value in zip(('TMP_btn', 'FW_desc7', 'TMP_result_ok', 'TMP_result_memory', 'TMP_result_failed'), values):
            pattern = r'^' + re.escape(key) + r'=.*$'
            count = len(re.findall(pattern, content, re.M))
            if count > 1:
                raise ValueError('Duplicate dictionary key: ' + key)
            if count:
                content = re.sub(pattern, lambda _: key + '=' + value, content, flags=re.M)
            else:
                content = content.rstrip('\n') + '\n' + key + '=' + value + '\n'
        dictionaries.append((path, content))
    # Resolve every anchor and dictionary before modifying the tree.
    for name in ('tmp-upload-guard.h', 'tmp-upload-policy.h'):
        shutil.copyfile(Path(__file__).with_name(name), http / name)
    source.write_text(modified, encoding='utf-8')
    page.write_text(response, encoding='utf-8')
    upgrade.write_text(upgrade_content, encoding='utf-8')
    for path, content in dictionaries:
        path.write_text(content, encoding='utf-8')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('root', type=Path)
    prepare(parser.parse_args().root)
