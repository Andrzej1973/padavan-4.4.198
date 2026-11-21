#!/usr/bin/env python3
"""Offline generated-metadata selection and bounds regression."""
import importlib.util
from pathlib import Path
import tempfile

spec=importlib.util.spec_from_file_location('provenance',Path(__file__).with_name('collect-curl-build-provenance.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with tempfile.TemporaryDirectory(prefix='wr-curl-provenance-') as temp:
    root=Path(temp)
    assert m.collect(root)['state']=='library tree missing'
    base=root/'trunk/libs';base.mkdir(parents=True)
    fixtures={
      'libnghttp2/nghttp2-1/build/CMakeCache.txt':'CMAKE_C_FLAGS:STRING=-fPIC -fvisibility=hidden\nIGNORED_VALUE:STRING=not-for-report\n',
      'libnghttp2/nghttp2-1/build/lib/CMakeFiles/nghttp2_static.dir/flags.make':'C_DEFINES = -DNGHTTP2_STATICLIB\n',
      'libcurl/curl-1/lib/Makefile':'LIBS = -lnghttp2 \\\n -lssl\nUNRELATED = not-for-report\n',
      'libcurl/curl-1/libtool':'archive_cmds="compiler --shared"\nunrelated="not-for-report"\n',
    }
    for name,content in fixtures.items():
        p=base/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
    escape=root/'outside';escape.write_text('must not copy')
    bad=base/'libcurl/curl-2/libtool';bad.parent.mkdir(parents=True);bad.symlink_to(escape)
    report=m.collect(root)
    assert len(report['files'])==4,report
    for entry in report['files'].values():
        assert 'not-for-report' not in '\n'.join(entry['selected_lines'])
        assert not entry['sample_truncated']
    key='libcurl/curl-1/lib/Makefile'
    assert report['files'][key]['selected_lines']==['LIBS = -lnghttp2 \\', ' -lssl']
    large=base/'libnghttp2/nghttp2-1/build/lib/CMakeFiles/nghttp2_static.dir/link.txt'
    large.write_bytes(b'x'*(m.LIMIT+10))
    assert m.collect(root)['files'][str(large.relative_to(base))]['sample_truncated']
print('PASS provenance selection, continuation, symlink escape refusal, missing tree and byte cap')
