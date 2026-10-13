#!/usr/bin/env python3
"""Exercise source transfer retries without network access or sleeping."""
import importlib.util
from pathlib import Path
import subprocess
import unittest

spec=importlib.util.spec_from_file_location('source_retry',Path(__file__).with_name('retry-source-command.py'))
retry=importlib.util.module_from_spec(spec);spec.loader.exec_module(retry)

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

if __name__=='__main__':unittest.main()
