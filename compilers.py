import os
import subprocess

import heuristic

class Executable:
  def __init__( self, path, command=[], add=True ):
    directory, filename = os.path.split(path)
    directory = '.' if directory == '' else directory
    path = os.path.join(directory, filename)
    self.path, self.command = path, list(command)
    if add:
      self.command.append(self.path)
  def __str__( self ):
    return self.path
  def start ( self, arguments=[], directory=None, stdin=None, stdout=None, stderr=None ):
    process = subprocess.Popen (
        self.command + list (arguments), cwd=directory, stdin=stdin, stdout=stdout, stderr=stderr
    )
    return process
  def __call__( self, *args, **kwargs ):
    process = self.start (*args, **kwargs)
    process.communicate ()
    return process.returncode == 0


compile_cache = {}

class Compiler:
  def __init__( self, name, *, binary=None, command=None, executable=None, t=None ):
    self.binary, self.command, self.executable = binary, command, executable
    if binary is None:
        self.binary = lambda source: source
    self.name = name
    self._t = t
  def __call__( self, source ):
    global log, compile_cache
    if not source.startswith ('/'):
        source = os.path.join (os.getcwd (), source)
    if source in compile_cache:
        return compile_cache[source]
    binary = self.binary(source)
    if binary == source or self.command is None or (os.path.isfile(binary) and os.stat(binary).st_mtime >= os.stat(source).st_mtime):
      self._t.log ('compile skipped: %s' % binary)
    else:
      self._t.log ('compile: %s → %s' % (source, binary))
      command = self.command(source, binary)
      self._t.log.debug ('$ %s' % (' '.join (command)))
      process = subprocess.Popen(command)
      process.communicate()
      if process.returncode != 0:
        return None
    compile_cache[source] = self.executable(binary)
    return compile_cache[source]


# === COMPILERS CONFIGURATION ==
# Здесь начинается конфигурация компиляторов. Мерзкая штука, не правда ли?


def compilers_configure ( configuration, t ):

    # script = lambda interpeter: lambda binary: Executable (binary, [interpeter])
    def script ( interpeter ):
        def result ( binary ):
            nonlocal interpeter
            return Executable (binary, [interpeter])
        return result

    executable_default = lambda binary: Executable (binary)
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
        'bash': Compiler ('bash', executable=script ('bash'), t=t),
        'perl': Compiler ('perl', executable=script ('perl'), t=t),
        'python2': Compiler ('python2', executable=script ('python2'), t=t),
        'python3': Compiler ('python3', executable=script ('python3'), t=t),
        'c': Compiler ('c',
            binary=binary_default,
            command=lambda source, binary: ['gcc'] + flags_c + ['-x', 'c', '-o', binary, source],
            executable=executable_default,
            t=t
        ),
        'c++': Compiler ('c++',
            binary=binary_default,
            command=lambda source, binary: ['g++'] + flags_cpp + ['-x', 'c++', '-o', binary, source],
            executable=executable_default,
            t=t
        ),
        'delphi': Compiler ('delphi',
            binary=binary_default,
            command=lambda source, binary: ['fpc', '-Mdelphi', '-O3', '-FE.', '-v0ewn', '-Sd', '-Fu' + include_path, '-Fi' + include_path, '-d__T_SH__', '-o'+binary, source],
            # command=lambda source, binary: ['fpc', '-Mdelphi', '-O3', '-FE.', '-v0ewn', '-Sd', '-d__T_SH__', '-o'+binary, source],
            executable=executable_default,
            t=t
        ),
        'java': Compiler ('java',
            binary=lambda source: os.path.splitext(source)[0] + '.class',
            command=lambda source, binary: ['javac', '-cp', os.path.dirname(source), source],
            executable=lambda binary: Executable (binary, [
                'java', '-Xms8M', '-Xmx128M', '-Xss64M', '-ea',
                '-cp', os.path.dirname (binary) + java_cp_suffix,
                os.path.splitext (os.path.basename (binary))[0]
            ], add=False),
            t=t
        ),
        'java.checker': Compiler ('java',
            binary=lambda source: os.path.splitext(source)[0] + '.class',
            command=lambda source, binary: ['javac', '-cp', os.path.dirname (source), source],
            executable=lambda binary: Executable (binary, [
                'java', '-Xms8M', '-Xmx128M', '-Xss64M', '-ea',
                "-cp", os.path.dirname(binary) + java_cp_suffix,
                "ru.ifmo.testlib.CheckerFramework", os.path.splitext (os.path.basename (binary))[0]
            ], add=False),
            t=t
        ),
        'pascal': Compiler ('pascal',
            binary=binary_default,
            command=lambda source, binary: [
                'fpc', '-O3', '-FE.', '-v0ewn', '-Fu' + include_path, '-Fi' + include_path,
                '-d__T_SH__', '-o'+binary, source
            ],
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


