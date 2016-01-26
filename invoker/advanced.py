#
#    t.py: utility for contest problem development
#    Copyright (C) 2009-2016 Oleg Davydov
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
import signal
import time
import threading
import subprocess

from tlib.common import Module
from .common import *


class Runner (Module):
    def __init__ ( self, *, limit_time=None, limit_idle=None, limit_memory=None, t ):
        super (Runner, self).__init__ (t=t)
        self.__limit_time = limit_time
        self.__limit_idle = limit_idle
        self.__limit_memory = limit_memory
        self.__process = None
        self.__condition = None
        if self.__limit_idle is not None:
            self._log.warning ("advanced runner doesn\'t support idleness timelimit")
        self._log.warning ("advanced runner doesn\'t support security limitations")

    def __waiter ( self ):
        self.__process.communicate ()
        self.__condition.acquire ()
        self.__condition.notify ()
        self.__condition.release ()

    def run ( self, *command, directory=None, stdin=None, stdout=None, stderr=None, verbose=False ):
        # TODO: twice upgrade invokation, use limit_idle
        # limit resources of current process: bad idea
        # resource.setrlimit(resource.RLIMIT_CPU, ((int)(self.limit_time + 2), -1))
        # resource.setrlimit(resource.RLIMIT_DATA, (self.limit_memory, -1))
        # useless case without rlimits
        # if code == -signal.SIGXCPU:
        #     return RunResult (RunResult.TIME_LIMIT, code, 'signal SIGXCPU received')
        time_start = time.time ()
        self.__process = subprocess.Popen (
            command, cwd=directory, stdin=stdin, stdout=stdout, stderr=stderr
        )
        pid = self.__process.pid
        self.__condition = threading.Condition ()
        thread = threading.Thread (target=self.__waiter)
        # wait, what?
        thread.start ()
        force_result = None
        mem_usage = 0
        while True:
            self.__condition.acquire()
            self.__condition.wait(0.01)
            self.__condition.release()
            if self.__process.returncode is not None:
                break
            try:  # так может случиться, что процесс завершится в самый интересный момент
                with open("/proc/%d/stat" % pid, 'r') as f:
                    stats = f.readline ().split ()
                with open("/proc/%d/statm" % pid, 'r') as f:
                    stats_m = f.readline ().split ()

                time_cpu = (int (stats[13]) + int (stats[14])) / \
                    os.sysconf (os.sysconf_names['SC_CLK_TCK'])
                time_real = time.time () - time_start
                mem_usage = int (stats_m[0]) * 1024

                line = "%.3fs, %.2fMiB" % (time_real, mem_usage / 2**20)
                line = line + '\b' * len (line)
                if verbose:
                    self._t.log (line, prefix=False, end='')

                if self.__limit_time is not None and time_cpu > self.__limit_time:
                    force_result = RunResult.limitTime ('cpu usage: %.2f' % time_cpu)
                    self.__process.kill ()
                if self.__limit_idle is not None and time_real > self.__limit_idle:
                    force_result = RunResult.limitIdle ('time usage: %.2f' % time_real)
                    self.__process.kill ()
                if self.__limit_memory is not None and mem_usage > self.__limit_memory:
                    force_result = RunResult.limitMemory ('memory usage: %d' % mem_usage)
                    self.__process.kill ()
            except IOError:
                pass
        time_real = time.time () - time_start
        line = "[%.3fs, %.2fMiB] " % (time_real, mem_usage / 2**20)
        if verbose:
            self._t.log (line, prefix=False, end='')
        if force_result is not None:
            return force_result
        code = self.__process.returncode
        if code != 0:
            return RunResult.runtime (code, 'runtime error %d' % code)
        else:
            return RunResult.ok ()

