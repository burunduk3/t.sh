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


import itertools
import os
import sys

from tlib.common import Error, Module
from .common import *

Runner = None

if Runner is None:
    try:
        from .advanced import Runner
    except ImportError as e:
        print ('advanced runner failed:', e, file=sys.stderr)
        pass

if Runner is None:
    try:
        from .basic import Runner
    except ImportError as e:
        print ('basic runner failed:', e, file=sys.stderr)
        pass

Error.ensure (Runner is not None, "failed to choose runner")


class Executable (Module):
    __default_runner = None

    def __init__ ( self, command, *, name=None, t):
        super (Executable, self).__init__ (t=t)
        self.__command = command
        if name is None:
            name = ' '.join (command)
        self.__name = name

    def __str__ ( self ):
        return self.__name

    def __call__ ( self, *args, runner=None, **kwargs ):
        if runner is None:
            if Executable.__default_runner is None:
                Executable.__default_runner = Runner (t=self._t)
            runner = Executable.__default_runner
        return runner.run (*itertools.chain (self.__command, args), **kwargs)

    @classmethod
    def local ( cls, path, *, t ):
        directory, filename = os.path.split (path)
        if directory == '':
            directory = '.'
        path = os.path.join (directory, filename)
        return cls ([path], name=path, t=t)


