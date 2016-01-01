import os
import subprocess

from common import Error, Module
import heuristic


class Executable:
    def __init__ ( self, command, *, name=None ):
        self.__command = command
        if name is None:
            name = ' '.join (command)
        self.__name = name

    def __str__ ( self ):
        return self.__name

    def start ( self, *arguments, directory=None, stdin=None, stdout=None, stderr=None ):
        process = subprocess.Popen (
            self.__command + list (arguments),
            cwd=directory, stdin=stdin, stdout=stdout, stderr=stderr
        )
        return process

    def __call__ ( self, *args, **kwargs ):
        process = self.start (*args, **kwargs)
        process.communicate ()
        return process.returncode == 0

    @classmethod
    def local ( cls, path ):
        directory, filename = os.path.split (path)
        if directory == '':
            directory = '.'
        path = os.path.join (directory, filename)
        return cls ([path], name=path)


class Compiler (Executable):
    def __init__ ( self, command, morph, *, name=None ):
        super (Compiler, self).__init__ (command, name=name)
        self.__morph = morph

    def compile ( self, source, target ):
        arguments = self.__morph (source, target)
        return self (*arguments)


compile_cache = {}


class Language (Module):
    def __init__( self, *, binary=None, compiler=None, executable=None, t ):
        super (Language, self).__init__ (t)
        self.__binary = binary
        self.__compiler = compiler
        self.__executable = executable
        if binary is None:
            self.__binary = lambda source: source

    def __call__( self, source ):
        global compile_cache
        key = source
        if not key.startswith ('/'):
            key = os.path.join (os.getcwd (), key)
        if key in compile_cache:
            return compile_cache[key]
        binary = self.__binary (source)
        need_recompile = True
        if self.__compiler is None:
            assert binary == source
            need_recompile = False
        if os.path.isfile (binary) and os.stat (binary).st_mtime >= os.stat (source).st_mtime:
            need_recompile = False
        if need_recompile:
            self._log ('compile: %s → %s' % (source, binary))
            if not self.__compiler.compile (source, binary):
                raise Error ("comilation failed: %s" % source)
        else:
            self._log ('compile skipped: %s' % binary)
        if not binary.startswith ('/'):
            binary = os.path.join (os.getcwd (), binary)
        compile_cache[key] = self.__executable (binary)
        return compile_cache[key]


