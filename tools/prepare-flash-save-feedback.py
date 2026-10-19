#!/usr/bin/env python3
"""Repair inherited flash-save feedback timers without changing CGI actions."""
import argparse
from pathlib import Path


def replace_once(text, old, new):
    if text.count(old) == 0 and text.count(new) == 1:
        return text
    if text.count(old) != 1 or new in text:
        raise ValueError('Unexpected flash-save feedback anchor: ' + old)
    return text.replace(old, new, 1)


def transform(page, state):
    old_error = 'setTimeout("reset_btn_commit("+$button+")", 1500);'
    old_success = 'setTimeout("reset_btn_commit(\'"+action_id+"\')", 1500);'
    callback = 'setTimeout(function(){ reset_btn_commit(action_id); }, 1500);'
    if page.count(callback) != 2 or old_error in page or old_success in page:
        if page.count(old_error) != 1 or page.count(old_success) != 1 or callback in page:
            raise ValueError('Unexpected settings-page flash-save feedback anchors')
        page = page.replace(old_error, callback, 1).replace(old_success, callback, 1)
    state = replace_once(state, 'setTimeout("reset_btn_commit(\'#commit_btn\')", 1500);',
        'setTimeout(function(){ reset_btn_commit("commit_btn"); }, 1500);')
    # The success callback must also avoid string evaluation. A distinct quote
    # style keeps the two idempotent anchors independently checkable.
    state = replace_once(state, 'setTimeout("reset_btn_commit(\'commit_btn\')", 1500);',
        "setTimeout(function(){ reset_btn_commit('commit_btn'); }, 1500);")
    page = replace_once(page, 'if(sys_result == 0)', 'if(sys_result === 0)')
    state = replace_once(state, 'if(sys_result == 0)', 'if(sys_result === 0)')
    return page, state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    www = args.source / 'trunk/user/www/n56u_ribbon_fixed'
    page, state = www / 'Advanced_SettingBackup_Content.asp', www / 'state.js'
    outputs = transform(page.read_text(encoding='utf-8'), state.read_text(encoding='utf-8'))
    for path, text in zip((page, state), outputs):
        path.write_text(text, encoding='utf-8', newline='\n')
    print('Prepared flash-save feedback callbacks; CGI actions and session gates preserved')


if __name__ == '__main__':
    main()
