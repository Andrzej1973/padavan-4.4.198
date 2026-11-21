#!/usr/bin/env python3
"""Exercise source transfer retries without network access or sleeping."""
import importlib.util
from pathlib import Path
import subprocess
import os
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('source_retry',Path(__file__).with_name('retry-source-command.py'))
retry=importlib.util.module_from_spec(spec);spec.loader.exec_module(retry)

def process_has_stopped(state):
    # /proc can vanish during read, including ESRCH after open succeeded.
    try:return state.read_text().split()[2] in ('Z','X')
    except (FileNotFoundError,ProcessLookupError):return True

class SourceRetryTests(unittest.TestCase):
    def run_case(self,outcomes):
        calls=[];pauses=[];iterator=iter(outcomes)
        command=['git','-C','path with spaces','fetch','origin','fixed-commit']
        def execute(argv,**options):
            calls.append((list(argv),options))
            outcome=next(iterator)
            if outcome=='timeout':raise subprocess.TimeoutExpired(argv,300)
            return subprocess.CompletedProcess(argv,outcome)
        status=retry.run(command,execute,pauses.append)
        for argv,options in calls:
            self.assertEqual(argv,command)
            self.assertEqual(options,{'timeout':300,'check':False})
        return status,len(calls),pauses

    def test_immediate_success(self):
        self.assertEqual(self.run_case([0]),(0,1,[]))

    def test_transient_failure(self):
        self.assertEqual(self.run_case([128,128,0]),(0,3,[10,20]))

    def test_persistent_failure(self):
        self.assertEqual(self.run_case([128,128,128]),(128,3,[10,20]))

    def test_timeout_recovery(self):
        self.assertEqual(self.run_case(['timeout',0]),(0,2,[10]))

    def test_persistent_timeout(self):
        self.assertEqual(self.run_case(['timeout']*3),(124,3,[10,20]))

    def test_signal_exit_remains_failure(self):
        self.assertEqual(self.run_case([-9]*3),(1,3,[10,20]))

    def test_configured_fetch_timeout(self):
        seen=[]
        def execute(argv,**options):
            seen.append(options['timeout'])
            return subprocess.CompletedProcess(argv,0)
        self.assertEqual(retry.run(['git','fetch'],execute,timeout=900),0)
        self.assertEqual(seen,[900])

    def test_cli_environment_timeout_and_explicit_override(self):
        script=str(Path(__file__).with_name('retry-source-command.py'))
        env=dict(os.environ,SOURCE_FETCH_TIMEOUT='0')
        command=[sys.executable,script,sys.executable,'-c','pass']
        failed=subprocess.run(command,env=env,capture_output=True,text=True)
        self.assertNotEqual(failed.returncode,0)
        self.assertIn('timeout must be 1..1800',failed.stderr)
        command=[sys.executable,script,'--timeout','900',sys.executable,'-c','pass']
        self.assertEqual(subprocess.run(command,env=env,capture_output=True).returncode,0)

    def test_process_disappears_during_proc_read(self):
        with patch.object(Path,'read_text',side_effect=ProcessLookupError):
            self.assertTrue(process_has_stopped(Path('/proc/fixture/stat')))
        with patch.object(Path,'read_text',side_effect=FileNotFoundError):
            self.assertTrue(process_has_stopped(Path('/proc/fixture/stat')))
        with patch.object(Path,'read_text',side_effect=PermissionError):
            with self.assertRaises(PermissionError):process_has_stopped(Path('/proc/fixture/stat'))

    @unittest.skipUnless(os.name=='posix','CI process groups require POSIX')
    def test_timeout_reaps_transport_and_only_own_new_lock(self):
        for existing in ('absent','regular','symlink'):
            with self.subTest(lock=existing),tempfile.TemporaryDirectory(prefix='source-retry-') as tmp:
                root=Path(tmp);(root/'bin').mkdir();(root/'padavan-4.4/.git').mkdir(parents=True)
                lock=root/'padavan-4.4/.git/shallow.lock'
                target=root/'preserved';target.write_text('preserved')
                if existing=='regular':lock.write_text('existing lock')
                if existing=='symlink':lock.symlink_to(target)
                fake=root/'bin/git'
                fake.write_text('#!'+sys.executable+'\n'+'''import pathlib,subprocess,sys,time
lock=pathlib.Path('padavan-4.4/.git/shallow.lock')
if not lock.exists():lock.write_text('owned by timed-out attempt')
child=subprocess.Popen([sys.executable,'-c','import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); time.sleep(60)'])
pathlib.Path('child.pid').write_text(str(child.pid))
time.sleep(60)
''')
                fake.chmod(0o755)
                previous=Path.cwd()
                try:
                    os.chdir(root)
                    with patch.dict(os.environ,{'PATH':str(root/'bin')+os.pathsep+os.environ['PATH']}):
                        with self.assertRaises(subprocess.TimeoutExpired):
                            retry.execute_source(['git','-C','padavan-4.4','fetch'],timeout=.4)
                    pid=int((root/'child.pid').read_text())
                    state=Path('/proc')/str(pid)/'stat'
                    for _ in range(50):
                        if process_has_stopped(state):break
                        time.sleep(.02)
                    self.assertTrue(process_has_stopped(state))
                    if existing=='absent':self.assertFalse(lock.exists())
                    elif existing=='regular':self.assertEqual(lock.read_text(),'existing lock')
                    else:self.assertTrue(lock.is_symlink())
                    self.assertEqual(target.read_text(),'preserved')
                finally:os.chdir(previous)

if __name__=='__main__':unittest.main()
