from pathlib import Path
import subprocess
import tempfile
from nvram_candidate_staging import stage
here=Path(__file__).resolve().parent
wire=(here.parent/'iot/native-flash-wire.h').read_bytes()
with tempfile.TemporaryDirectory(prefix='wr-nvram-stage-') as directory:
    root=Path(directory);production=root/'production';production.mkdir()
    for name in ('nvram.c','nvram_linux.c','Makefile'):
        (production/name).write_text('baseline\n')
    target=root/'original';target.mkdir()
    assert set(stage(production,target))=={'nvram.c','nvram_linux.c','Makefile'}
    (production/'nvram_linux.c').write_text('#include "wr-nvram-flash-wire.h"\n')
    for case in ('missing','mismatch','symlink'):
        header=production/'wr-nvram-flash-wire.h'
        if header.exists() or header.is_symlink():header.unlink()
        if case=='mismatch':header.write_bytes(wire+b'changed')
        if case=='symlink':header.symlink_to(here.parent/'iot/native-flash-wire.h')
        target=root/case;target.mkdir()
        try:stage(production,target)
        except ValueError:pass
        else:raise AssertionError('Invalid dependency must refuse: '+case)
        assert not list(target.iterdir())
    header.unlink();header.write_bytes(wire)
    before={path.name:path.read_bytes() for path in production.iterdir()}
    target=root/'prepared';target.mkdir()
    assert 'wr-nvram-flash-wire.h' in stage(production,target)
    assert {path.name:path.read_bytes() for path in production.iterdir()}==before
    assert {path.name:path.read_bytes() for path in target.iterdir()}==before
    try:stage(production,target)
    except ValueError:pass
    else:raise AssertionError('Repeated staging must refuse')
    probe=target/'probe.c';binary=target/'probe'
    probe.write_text('#include "wr-nvram-flash-wire.h"\n_Static_assert(sizeof(struct wr_nvram_save_profile)==400,"wire size");\nint main(void){return 0;}\n')
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-I'+str(target),str(probe),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True,timeout=5)
print('PASS isolated native source staging: original three files, exact required flash wire copied, missing/drift/symlink/repeat refused before writes, production unchanged and staged include compiles; host only')
