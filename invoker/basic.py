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
import sys

from .common import *
from tlib import Module

class Runner (Module):
    def __init__ ( self, *, limit_time=None, limit_idle=None, limit_memory=None, t ):
        super (Runner, self).__init__ (t=t)
        if limit_time is not None:
            self._log.warning ("basic runner doesn't support time limit")
        if limit_idle is not None:
            self._log.warning ("basic runner doesn\'t support time limit")
        if limit_memory is not None:
            self._log.warning ("basic runner doesn\'t support memory limit")
        self._log.warning ("basic runner doesn\'t support security limitations")

    def __enter__ ( self ):
        if self.__directory is not None:
            self.__directory_old = os.getcwd ()
            os.chdir (self.__directory)
        if self.__stdin:
            self.__stdin_fd = os.dup (sys.stdin.fileno ())
            os.dup2 (self.__stdin.fileno (), sys.stdin.fileno ())
        if self.__stdout:
            self.__stdout_fd = os.dup (sys.stdout.fileno ())
            os.dup2 (self.__stdout.fileno (), sys.stdout.fileno ())
        if self.__stderr:
            self.__stderr_fd = os.dup (sys.stderr.fileno ())
            os.dup2 (self.__stderr.fileno (), sys.stderr.fileno ())

    def __exit__ ( self, *args ):
        # «А если будут яйца — возьми десяток»
        if self.__directory is not None:
           os.chdir (self.__directory_old)
        if self.__stdin:
           os.dup2 (self.__stdin_fd, sys.stdin.fileno ())
           os.close (self.__stdin_fd)
        if self.__stdout:
           os.dup2 (self.__stdout_fd, sys.stdout.fileno ())
           os.close (self.__stdout_fd)
        if self.__stderr:
           os.dup2 (self.__stderr_fd, sys.stderr.fileno ())
           os.close (self.__stderr_fd)

    def run ( self, *command, directory=None, stdin=None, stdout=None, stderr=None, verbose=False ):
        self.__stdin = stdin
        self.__stdout = stdout
        self.__stderr = stderr
        for x in command:
            self._ensure (' ' not in x, "basic invoker doesn't support space in arguments")
        self.__directory = directory
        with self:
            r = os.system (' '.join (command))
        return RunResult.exitCode (r)

