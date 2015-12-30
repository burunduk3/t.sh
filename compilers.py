import os
import subprocess

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

class Language:
  def __init__( self, name, *, binary=None, compiler=None, executable=None, t=None ):
    self.binary, self.__compiler, self.executable = binary, compiler, executable
    if binary is None:
        self.binary = lambda source: source
    self.name = name
    self._t = t
  def __call__( self, source ):
    global compile_cache
    key = source
    if not key.startswith ('/'):
        key = os.path.join (os.getcwd (), key)
    if key in compile_cache:
        return compile_cache[key]
    binary = self.binary(source)
    if binary == source or self.__compiler is None or (os.path.isfile(binary) and os.stat(binary).st_mtime >= os.stat(source).st_mtime):
      self._t.log ('compile skipped: %s' % binary)
    else:
      self._t.log ('compile: %s → %s' % (source, binary))
      if not self.__compiler.compile (source, binary):
          return None  # TODO: raise t.Error?
    if not binary.startswith ('/'):
        binary = os.path.join (os.getcwd (), binary)
    compile_cache[key] = self.executable(binary)
    return compile_cache[key]


# === COMPILERS CONFIGURATION ==
# Здесь начинается конфигурация компиляторов. Мерзкая штука, не правда ли?


def compilers_configure ( configuration, t ):

    # script = lambda interpeter: lambda binary: Executable (binary, [interpeter])
    def script ( interpeter ):
        def result ( binary ):
            nonlocal interpeter
            return Executable ([interpeter, binary])
        return result

    executable_default = lambda binary: Executable.local (binary)
    binary_default = lambda source: os.path.splitext(source)[0]

    java_cp_suffix = os.environ.get('CLASSPATH', None)
    if java_cp_suffix is None:
        java_cp_suffix = ""
    else:
        java_cp_suffix = ":" + java_cp_suffix

    # something strange
    # include_path = '../../../include/testlib.ifmo'
    # include_path = '/home/burunduk3/user/include/testlib.ifmo'
    include_path = '/home/burunduk3/user/include'
    flags_c = ['-O2', '-Wall', '-Wextra', '-D__T_SH__', '-lm'] + os.environ['CFLAGS'].split()
    flags_cpp = ['-O2', '-Wall', '-Wextra', '-D__T_SH__', '-lm'] + os.environ['CXXFLAGS'].split()

    compilers = {
        'bash': Language ('bash', executable=script ('bash'), t=t),
        'perl': Language ('perl', executable=script ('perl'), t=t),
        'python2': Language ('python2', executable=script ('python2'), t=t),
        'python3': Language ('python3', executable=script ('python3'), t=t),
        'c': Language ('c',
            binary=binary_default,
            compiler=Compiler (
                ['gcc'] + flags_c + ['-x', 'c'],
                lambda source, target: ['-o', target, source],
                name='c.gcc'
            ),
            executable=executable_default,
            t=t
        ),
        'c++': Language ('c++',
            binary=binary_default,
            compiler=Compiler (
                ['g++'] + flags_cpp + ['-x', 'c++'],
                lambda source, target: ['-o', target, source],
                name='c++.gcc'
            ),
            executable=executable_default,
            t=t
        ),
        'delphi': Language ('delphi',
            binary=binary_default,
            compiler=Compiler (
                ['fpc', '-Mdelphi', '-O3', '-FE.', '-v0ewn', '-Sd', '-Fu' + include_path, '-Fi' + include_path, '-d__T_SH__'],
                lambda source, target: ['-o' + target, source],
                name='delphi.fpc'
            ),
            # command=lambda source, binary: ['fpc', '-Mdelphi', '-O3', '-FE.', '-v0ewn', '-Sd', '-d__T_SH__', '-o'+binary, source],
            executable=executable_default,
            t=t
        ),
        'java': Language ('java',
            binary=lambda source: os.path.splitext(source)[0] + '.class',
            compiler=Compiler (
               ['javac'],
               lambda source, target: ['-cp', os.path.dirname (source), source],
               name='java'
            ),
            executable=lambda binary: Executable ([
                'java', '-Xms8M', '-Xmx128M', '-Xss64M', '-ea',
                '-cp', os.path.dirname (binary) + java_cp_suffix,
                os.path.splitext (os.path.basename (binary))[0]
            ], name=binary),
            t=t
        ),
        'java.checker': Language ('java',
            binary=lambda source: os.path.splitext(source)[0] + '.class',
            compiler=Compiler (
               ['javac'],
               lambda source, target: ['-cp', os.path.dirname (source), source],
               name='checker.java'
            ),
            executable=lambda binary: Executable ([
                'java', '-Xms8M', '-Xmx128M', '-Xss64M', '-ea',
                "-cp", os.path.dirname(binary) + java_cp_suffix,
                "ru.ifmo.testlib.CheckerFramework", os.path.splitext (os.path.basename (binary))[0]
            ], name=binary),
            t=t
        ),
        'pascal': Language ('pascal',
            binary=binary_default,
            compiler=Compiler (
                ['fpc', '-O3', '-FE.', '-v0ewn', '-Fu' + include_path, '-Fi' + include_path, '-d__T_SH__'],
                lambda source, target: ['-o' + target, source],
                name='pascal.fpc'
            ),
            executable=executable_default,
            t=t
        ),
    }
    heuristic.set_compilers (compilers)

    if configuration is None:
        return

    configuration.compilers = compilers

    def detector_python( source ):
        with open (source, 'r') as f:
            shebang = f.readline ()
            if shebang[0:2] != '#!':
                shebang = ''
            if 'python3' in shebang:
                return 'python3'
            elif 'python2' in shebang:
                return 'python2'
            else:
                # python3 is default
                return 'python3'

    configuration.detector = {
        'c': 'c', 'c++': 'c++', 'C': 'c++', 'cxx': 'c++', 'cpp': 'c++',
        'pas': 'pascal', 'dpr': 'delphi',
        'java': 'java', 'pl': 'perl', 'py': detector_python, 'sh': 'bash'
    }


