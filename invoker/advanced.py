#
#    t.py: utility for contest problem development
#    Copyright (C) 2009-2017 Oleg Davydov
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import os
import time
import resource
import subprocess

from tlib import Log, Module
from .common import *


class Process:
    class CONTINUE:
        pass

    def __init__ ( self,
        command, *,
        directory=None,
        stdin=None, stdout=None, stderr=None,
        limit_time=None, limit_idle=None, limit_memory=None
    ):
        self.__start = time.time ()
        if type (stdin) is str:
            stdin = open (stdin, "rb")
        if type (stdout) is str:
            stdout = open (stdout, "wb")
        if type (stderr) is str:
            stderr = open (stderr, "wb")
        self.__popen = subprocess.Popen (
            command, cwd=directory, stdin=stdin, stdout=stdout, stderr=stderr
        )
        self.__pid = self.__popen.pid
        self.__limit_time = limit_time
        self.__limit_idle = limit_idle
        self.__limit_memory = limit_memory
        self.__usage_time = 0.0
        self.__usage_idle = 0.0
        self.__usage_memory = 0
        self.__peak_memory = 0

    usage_time = property (lambda self: self.__usage_time)
    usage_memory = property (lambda self: self.__usage_memory)
    peak_memory = property (lambda self: self.__peak_memory)

    def peaks ( self ):
        return {
            'peak_time': self.__usage_time,
            'peak_memory': self.__peak_memory
        }

    def check ( self ):
        code = self.__popen.returncode
        if code is not None:
            return code
        try:  # так может случиться, что процесс завершится в самый интересный момент
            with open("/proc/%d/stat" % self.__pid, 'r') as f:
                stats = f.readline ().split ()
            with open("/proc/%d/statm" % self.__pid, 'r') as f:
                stats_m = f.readline ().split ()

            self.__usage_time = (int (stats[13]) + int (stats[14])) / \
                os.sysconf (os.sysconf_names['SC_CLK_TCK'])
            self.__usage_idle = time.time () - self.__start
            self.__usage_memory = int (stats_m[0]) * 1024
            self.__peak_memory = max (self.__peak_memory, self.__usage_memory)

            if self.__limit_time is not None and self.__usage_time > self.__limit_time:
                return RunResult.limitTime ('cpu usage: %.2f' % self.__usage_time, **self.peaks ())
                self.__popen.kill ()
            if self.__limit_idle is not None and self.__usage_idle > self.__limit_idle:
                return RunResult.limitIdle ('time usage: %.2f' % self.__usage_idle, **self.peaks ())
                self.__popen.kill ()
            if self.__limit_memory is not None and self.__usage_memory > self.__limit_memory:
                return RunResult.limitMemory ('memory usage: %d' % self.__usage_memory, **self.peaks ())
                self.__popen.kill ()

            return Process.CONTINUE
        except IOError:
            return None

    def kill ( self ):
        return self.__popen.kill ()

    def communicate ( self, *args, **kwargs ):
        return self.__popen.communicate (*args, **kwargs)


class Runner (Module):
    def __init__ ( self, *, t ):
        super (Runner, self).__init__ (t=t)
        resource.setrlimit (resource.RLIMIT_STACK, (-1, -1))  # set unlimited stack size
        self._log.warning ("advanced runner doesn\'t support security limitations")

    def run (self,
        command, *,
        interactor=None,
        wait=True,
        verbose=False,
        stdin=None, stdout=None, stderr=None,
        **kwargs
    ):
        if stdin is None:
            stdin = subprocess.DEVNULL
        if stdout is None and self._log.policy is Log.BRIEF:
            stdout = subprocess.DEVNULL
        if stderr is None and self._log.policy is Log.BRIEF:
            stderr = subprocess.DEVNULL
        process = Process (command, stdin=stdin, stdout=stdout, stderr=stderr, **kwargs)
        if not wait:
            return process
        outputs = None
        try:
            time_cpu = 0.0
            while True:
                result_process = process.check ()
                if result_process is None:
                    continue
                if isinstance (result_process, (RunResult, int)):
                    break
                if interactor is not None:
                    result_interactor = interactor.check ()
                    if result_interactor is None:
                        continue
                    # self._log.debug ("interactor result: ", result_interactor)
                    if isinstance (result_interactor, (RunResult, int)):
                        process.kill ()
                if verbose:
                    line = "%.3fs, %.2fMiB" % (process.usage_time, process.usage_memory / 2**20)
                    line = line + '\b' * len (line)
                    self._t.log (line, prefix=False, end='')
                try:
                    outputs = process.communicate (timeout=0.01)
                except subprocess.TimeoutExpired:
                    pass
                if interactor is not None:
                    try:
                        # self._log.debug ("interactor.communicate")
                        interactor.communicate (timeout=0)
                    except subprocess.TimeoutExpired:
                        pass
            if interactor is not None:
                interactor.communicate ()
                result_interactor = interactor.check ()
        finally:
            if interactor is not None:
                interactor.kill ()
            process.kill ()
        
        if outputs is None:
            outputs = process.communicate ()
        if isinstance (result_process, int) and result_process:
            result_process = RunResult.runtime (result_process, 'exit code: %d' % result_process, outputs=outputs, **process.peaks ())
        if isinstance (result_process, int) and result_process == 0:
            result_process = RunResult.ok (outputs=outputs, **process.peaks ())
        if verbose:
            line = "[%.3fs, %.2fMiB] " % (process.usage_time, process.peak_memory / 2**20)
            self._t.log (line, prefix=False, end='')
        assert type (result_process) is RunResult
        if interactor is not None:
            if isinstance (result_interactor, int) and result_interactor:
                result_interactor = RunResult.runtime (result_interactor, 'exit code: %d' % result_interactor, **interactor.peaks ())
            if isinstance (result_interactor, int) and result_interactor == 0:
                result_interactor = RunResult.ok (**interactor.peaks ())
            assert type (result_interactor) is RunResult
            return (result_interactor, result_process)
        return result_process

