"""Compose native ra2 mutation wrappers plus their Linux admission implementation.

Preparation only: not called by the candidate installer until insertion and
both key-writer bindings participate in the same arbitration protocol.
"""
import runpy


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('mutation binding anchor changed: ' + old)
    return text.replace(old, new, 1)


def compose(changes, src, local):
    result = dict(changes)
    def get(name):
        return result.get(name, (src/name).read_text())
    header = get('include/rtmp.h')
    if 'struct wr_ra2_assoc_owner wr_ra2_assoc_owner;' in header:
        raise ValueError('mutation binding already installed')
    header = replace_once(header, 'typedef struct _MAC_TABLE_ENTRY {',
        '#include "ra2-association-owner.h"\ntypedef struct _MAC_TABLE_ENTRY {')
    header = replace_once(header, ' unsigned int wr_iot_ra2_key_active;',
        ' unsigned int wr_iot_ra2_key_active;\n struct wr_ra2_assoc_owner wr_ra2_assoc_owner;')
    result['include/rtmp.h'] = header
    module = runpy.run_path(str(local/'ra2-mutation-wrappers.py'))
    for name in module['SITES']:
        text, _ = module['compose'](name, get(name))
        text = replace_once(text, '#include "rt_config.h"',
            '#include "rt_config.h"\n'+module['GUARD']+
            '\n#include "ra2-mutation-admission-kernel.h"\n#endif')
        result[name] = text
    for name in ('ra2-association-owner.h', 'ra2-mutation-admission-kernel.h'):
        result['include/'+name] = (local/name).read_text()
    return result
