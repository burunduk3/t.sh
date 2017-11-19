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

from tlib import Color, Error, Log, Module


class CompilationError (Error):
    def __init__ ( self, source, *args, **kwargs ):
        super (CompilationError, self).__init__ (*args, **kwargs)
        self.__source = source

    def __str__ ( self ):
        return "compilation failed: %s" % self.__source


class Compiler (Module):
    def __init__ (
        self, name, *args,
        binary=lambda source: source.path, compile=None, executable, suffixes=[], **kwargs
    ):
        """
            binary: Source -> binary name
            compile: Source, binary name -> RunResult for compilation
            executable: binary name, Source -> Executable
        """
        super (Compiler, self).__init__ (*args, **kwargs)
        self.__name = name
        self.__suffixes = suffixes
        self.__binary = binary
        self.__compile = compile
        self.__executable = executable

    name = property (lambda self: self.__name)
    suffixes = property (lambda self: self.__suffixes)
    binary = property (lambda self: self.__binary)
    executable = property (lambda self: self.__executable)

    def __call__ ( self, source, directory=None ):
        binary = self.__binary (source)
        if self.__compile is not None:
            compile, args = self.__compile (source, binary)
            if self._log.policy is not Log.BRIEF:
                self._log (
                    '[compile %s]' % source, Color.DEFAULT, ' $ ' + str (compile) + ' '.join (args)
                )
            result = compile.run (args, directory=directory)
            if not result:
                raise self._error (source, cls=CompilationError)
        else:
            assert binary == source.path
        return self.__executable (binary, source)


