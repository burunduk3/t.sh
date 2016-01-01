#
#    t.py: utility for contest problem development
#    Copyright (C) 2009-2015 Oleg Davydov
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

import os.path

import common
import compilers
from datalog import Datalog
import problem


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

suffixes = {
    'c': 'c', 'c++': 'c++', 'C': 'c++', 'cxx': 'c++', 'cpp': 'c++',
    'pas': 'pascal', 'dpr': 'delphi',
    'java': 'java', 'pl': 'perl', 'py': detector_python, 'sh': 'bash'
}


def suffixes_all ():
    return suffixes.keys ()


def compiler_detect ( path ):
    suffix = path.split ('.')[-1]
    try:
        detector = suffixes[suffix]
    except KeyError as error:
        return None
    if isinstance (detector, str):
        return detector
    return detector (path)


def set_compilers ( value ):
    global languages
    languages = value


class Source:
    def __init__ ( self, path, compiler=None ):
        self.__path = path
        self.__compiler = compiler
        assert compiler is not None
        self.__executable = None

    def __str__ ( self ):
        return self.__path

    def __eq__ ( self, other ):
        return type (other) is Source and \
            self.__path == other.__path and \
            self.__compiler == other.__compiler

    def compile ( self ):
        global languages 
        compiler = languages[self.__compiler]
        self.__executable = compiler (self.__path)
        if self.__executable is None:
            raise common.Error ("%s: compilation error" % self.__path)

    def run ( self, *arguments, **kwargs ):
        if self.__executable is None:
            self.compile ()
        return self.__executable (*arguments, **kwargs)

    path = property (lambda self: self.__path)
    compiler = property (lambda self: self.__compiler)
    executable = property (lambda self: self.__executable)

    @classmethod
    def find ( cls, path, *, prefix=None, directory=None ):
        for filename in [path + '.' + suffix for suffix in suffixes.keys ()] + [path]:
            if directory is not None:
                real = os.path.join (directory, filename)
            else:
                real = filename
            if not os.path.isfile (real):
                continue
            compiler = compiler_detect (real)
            if compiler is not None:
                return cls (real, compiler)
        if prefix is not None:
            return Source.find (prefix + '_' + path, directory=directory)
        return None


def find_problems ( base='.', *, t ):
    queue = [os.path.abspath (base)]
    for path in queue:
        if not os.path.isdir(path):
            continue
        is_problem = False
        for marker in ['.datalog', 'problem.xml', 'problem.properties', 'source', 'src', 'tests']:
            if os.path.exists (os.path.join (path, marker)):
                is_problem = True
                break
        if is_problem:
            yield problem_open (path, t=t)
        else:
            queue += [os.path.join (path, x) for x in sorted (os.listdir (path))]


#
# FORCED OPTIONS
#
#  ~~~~~~~~~~~~
# ~ HOW TO USE ~
#  ~~~~~~~~~~~~
#
# 1) Scan problem.xml/problem.properties/etc and save options.
# 2) Traverse problem options in canonical order.
# 2.1) If option is forced, set it.
# 2.2) Else if options is calculated, set it. Canonical order will guarantee.
#

def problem_force_xml ( path, *, t ):
    try:
        with open (os.path.join (path, 'problem.xml'), 'r'):
            raise Exception ("TODO: parse problem.xml")
    except FileNotFoundError:
        return None  # no file, no problems
    assert False


def problem_properties_parse ( path ):
    with open (path, 'r') as f:
        for line in f.readlines ():
            key, value = [token.strip() for token in line.split('=', 1)]
            if value[0] == '"' and value[-1] == '"':
                value = value[1:-1]
            yield key, value


def solution_find ( token, problem ):
    result = Source.find (token)
    if result is not None:
        return result
    result = Source.find (problem.name_short + '_' + token)
    if result is not None:
        return result
    return None


def problem_force_properties ( path, *, t ):
    try:
        properties = problem_properties_parse (os.path.join (path, 'problem.properties'))
        result = {}
        options = {
            'time-limit': ('time limit', lambda x: lambda y: float (x)),
            'idle-limit': ('idle limit', lambda x: lambda y: float (x)),
            'memory-limit': ('memory limit',
                lambda x: lambda problem: problem.parse_memory (x, t=t)),
            'input-file': ('input', lambda x: lambda problem: problem.parse_file (x, t=t)),
            'output-file': ('output', lambda x: lambda problem: problem.parse_file (x, t=t)),
            'solution': ('solution', lambda x: lambda problem: solution_find (x, problem))
            # TODO: configure checker, validator…
            # if 'checker' in problem_configuration:
            #   checker_name = problem_configuration['checker']
            #  if checker_name.startswith('testlib/'):
            #    # TODO: configure checker path somewhere
            #    checker_name = '/home/burunduk3/code/testlib-ro/' +
            #    'trunk/checkers/' + checker_name[8:] + '.cpp'
            #  checker = find_source(checker_name)
        }
        for name, value in properties:
            try:
                key, morph = options[name]
            except KeyError:
                self._t.log.warning ('[%s]: ignored option: %s' % (path, name))
                continue
            assert key not in result
            result[key] = morph (value)
    except FileNotFoundError:
        return None  # no file, no problems

    return result


def problem_force_auto ( path, *, t ):
    for d in ['source', 'src', 'tests']:
        if os.path.isdir (os.path.join (path, d)):
            return {}
    return None


def problem_open ( path=os.path.abspath ('.'), datalog='.datalog', *, t):
    force = None
    if force is None:
        force = problem_force_xml (path, t=t)
    if force is None:
        force = problem_force_properties (path, t=t)
    if force is None:
        force = problem_force_auto (path, t=t)
    try:
        p = problem.Problem (os.path.join (path, datalog), create=(force is not None), t=t)
    except Datalog.NotFound as error:
        raise common.Error ("not a problem: '%s'" % path) from error
    if p.uuid is None:
        p.create ()
    if force is None:
        force = {}
    defaults = {
        'name': lambda: os.path.basename (p.path),
        'time limit': lambda: 5.0,
        'idle limit': lambda: 10.0,
        'memory limit': lambda: 768 * 2**20,  # 768 MiB
        # TODO: mode autodetect here, fix output
        # 'generator', lambda: self.__autodetect_generator ()),
        # 'validator', lambda: self.validator, lambda: self.__autodetect_validator ()),
        # 'checker', lambda: self.checker, lambda: self.__autodetect_checker ())
        # for name, key, setter in detectors:
        #     if not setter ():
        #         continue
        #     self._t.log.notice ("[p %s]: found %s: %s" % (self.name, name, key ()))
    }
    os.chdir (p.path)

    def routine ( key, getter, setter, default ):
        nonlocal p, t
        value = getter ()
        if key in force:
            value_new = force[key] (p)
            if value_new != value:
                t.log ('[problem %s] set %s to %s' % (p.name, key, value_new))
                setter (value_new)
            return
        if value is not None:
            return
        # TODO: semidefaults
        if key in defaults:
            setter (defaults[key] ())
        elif default is not None:
            default ()
        if getter () is None:
            return
        t.log.warning ("[problem %s] %s isn't set, use default (%s)" % (
            p.name, key, getter ()
        ))

    p.canonical (routine)
    return p


# === COMPILERS CONFIGURATION ==
# Здесь начинается конфигурация компиляторов. Мерзкая штука, не правда ли?
# TODO: move to heuristics

def compilers_configure ( configuration, t ):

    # script = lambda interpeter: lambda binary: Executable (binary, [interpeter])
    def script ( interpeter ):
        def result ( binary ):
            nonlocal interpeter
            return compilers.Executable ([interpeter, binary])
        return result

    executable_default = lambda binary: compilers.Executable.local (binary)
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

    L = compilers.Language
    C = compilers.Compiler
    E = compilers.Executable
    result = {
        'bash': L (executable=script ('bash'), t=t),
        'perl': L (executable=script ('perl'), t=t),
        'python2': L (executable=script ('python2'), t=t),
        'python3': L (executable=script ('python3'), t=t),
        'c': L (
            binary=binary_default,
            compiler=C (
                ['gcc'] + flags_c + ['-x', 'c'],
                lambda source, target: ['-o', target, source],
                name='c.gcc'
            ),
            executable=executable_default,
            t=t
        ),
        'c++': L (
            binary=binary_default,
            compiler=C (
                ['g++'] + flags_cpp + ['-x', 'c++'],
                lambda source, target: ['-o', target, source],
                name='c++.gcc'
            ),
            executable=executable_default,
            t=t
        ),
        'delphi': L (
            binary=binary_default,
            compiler=C (
                [
                    'fpc', '-Mdelphi', '-O3', '-FE.', '-v0ewn', '-Sd', '-Fu' + include_path,
                    '-Fi' + include_path, '-d__T_SH__'
                ],
                lambda source, target: ['-o' + target, source],
                name='delphi.fpc'
            ),
            # command=lambda source, binary: [
            #     'fpc', '-Mdelphi', '-O3', '-FE.', '-v0ewn', '-Sd', '-d__T_SH__',
            #     '-o'+binary, source
            # ],
            executable=executable_default,
            t=t
        ),
        'java': L (
            binary=lambda source: os.path.splitext (source)[0] + '.class',
            compiler=C (
                ['javac'],
                lambda source, target: ['-cp', os.path.dirname (source), source],
                name='java'
            ),
            executable=lambda binary: E ([
                'java', '-Xms8M', '-Xmx128M', '-Xss64M', '-ea',
                '-cp', os.path.dirname (binary) + java_cp_suffix,
                os.path.splitext (os.path.basename (binary))[0]
            ], name=binary),
            t=t
        ),
        'java.checker': L (
            binary=lambda source: os.path.splitext(source)[0] + '.class',
            compiler=C (
                ['javac'],
                lambda source, target: ['-cp', os.path.dirname (source), source],
                name='checker.java'
            ),
            executable=lambda binary: E ([
                'java', '-Xms8M', '-Xmx128M', '-Xss64M', '-ea',
                "-cp", os.path.dirname(binary) + java_cp_suffix,
                "ru.ifmo.testlib.CheckerFramework", os.path.splitext (os.path.basename (binary))[0]
            ], name=binary),
            t=t
        ),
        'pascal': L (
            binary=binary_default,
            compiler=C (
                [
                    'fpc', '-O3', '-FE.', '-v0ewn', '-Fu' + include_path, '-Fi' + include_path,
                    '-d__T_SH__'
                ],
                lambda source, target: ['-o' + target, source],
                name='pascal.fpc'
            ),
            executable=executable_default,
            t=t
        ),
    }
    set_compilers (result)

    if configuration is None:
        return

    configuration.compilers = result

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


