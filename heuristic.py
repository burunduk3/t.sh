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

import os.path

from tlib.common import Error
from tlib.datalog import Datalog, Type
from tlib import types
import compilers
import problem

import xml.etree.ElementTree as xml


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


def source_find ( path, *, prefix=None, directory=None ):
    global languages
    for filename in [path + '.' + suffix for suffix in suffixes.keys ()] + [path]:
        if directory is not None:
            real = os.path.join (directory, filename)
        else:
            real = filename
        if not os.path.isfile (real):
            continue
        compiler = compiler_detect (real)
        if compiler is not None:
            return types.Source (real, compiler, languages)
    if prefix is not None:
        return source_find (prefix + '_' + path, directory=directory)
    return None


def find_problems ( base='.', *, datalog_write=True, t ):
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
            yield problem_open (path, datalog_write=datalog_write, t=t)
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
        with open (os.path.join (path, 'problem.xml'), 'r') as f:
            data = f.read ()
    except FileNotFoundError:
        return None  # no file, no problems
    data = xml.XML (data)
    if list (sorted (data.attrib.keys ())) == ['id', 'version'] and data.attrib['version'] == "1.0":
        t.log.info ("ignore problem.xml: not problem data but config for PCMS2")
        return None
    print (data.tag, data.text, data.attrib)
    raise Exception ("TODO: parse problem.xml")


def problem_properties_parse ( path, *, t ):
    with open (path, 'r') as f:
        for line in f.readlines ():
            line = line.strip ()
            if line == '':
                continue
            try:
                key, value = [token.strip() for token in line.split('=', 1)]
            except ValueError:
                t.log ("problem.properties: bad line '%s'" % line)
                continue
            if value[0] == '"' and value[-1] == '"':
                value = value[1:-1]
            yield key, value


def solution_find ( token, problem ):
    result = source_find (token)
    if result is not None:
        return result
    result = source_find (problem.name_short + '_' + token)
    if result is not None:
        return result
    return None


def problem_force_properties ( path, *, t ):
    try:
        properties = problem_properties_parse (os.path.join (path, 'problem.properties'), t=t)
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
                t.log.warning ('[%s]: ignored option: %s' % (path, name))
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


# TODO: for files copy
# def convert_tests( tests ):
#   log('convert tests', end='')
#   for test in tests:
#     log.write('.')
#     p = subprocess.Popen(['dos2unix', test], stderr=open('/dev/null', 'w'))
#     p.communicate()
#     if p.returncode != 0: log.warning('dos2unix failed on test %s' % test)
#     if not os.path.isfile(test + '.a'):
#       continue
#     p = subprocess.Popen(['dos2unix', test + '.a'], stderr=open('/dev/null', 'w'))
#     p.communicate()
#     if p.returncode != 0: log.warning('dos2unix failed on file %s.a' % test)
#   log.write('done\n')

class AutoGenerator (Type):
    LEV = 'problem.generator.auto'

    def __init__ ( self, problem, *, t ):
        super (AutoGenerator, self).__init__ (t=t)
        self.__problem = problem

    def __str__ ( self ):
        return '<generator:automatic>'

    def __eq__ ( self, x ):
        return type (self) is type (x)

    def commit ( self ):
        return (AutoGenerator.LEV,)

    def run ( self ):
        directory = 'source'
        if not os.path.isdir (directory):
            directory = 'src'
        if not os.path.isdir (directory):
            directory = 'tests'
        if not os.path.isdir (directory):
            raise Error ('[problem %s]: failed to find source directory' % self.__problem.name)
        count_hand, count_gen, failure = 0, 0, False
        # TODO: this is slow on some outdated systems
        for test in ['%02d' % i for i in range (100)]:
            target = os.path.join ('.tests', '%d' % (count_hand + count_gen))
            for f in [os.path.join (directory, test + suffix) for suffix in ['.hand', '.manual']]:
                if not os.path.isfile (f):
                    continue
                shutil.copy (f, target)
                count_hand += 1
                break
            else:
                generator = source_find ('do' + test)
                if generator is None:
                    generator = source_find ('gen' + test)
                if generator is None:
                    continue
                result = generator.run (stdout=open (target, 'w'))
                if not result:
                    raise Error ('generator (%s) failed' % generator)
                    failure = True
                else:
                    count_gen += 1
        if count_hand != 0:
            self._log ('manual tests copied: %d' % count_hand)
        if count_gen != 0:
            self._.log ('generated tests: %d' % count_gen)
        return not failure

    @classmethod
    def set ( cls, problem, *, t ):
        return cls (problem, t=t)

    @classmethod
    def register ( cls, *, t ):
        t.register_problem_upgrade (
            problem.Problem.TYPE_GENERATOR,
            AutoGenerator.LEV,
            lambda problem, data, cls=cls, t=t: cls.set (problem, t=t)
        )


def problem_open ( path=os.path.abspath ('.'), datalog='.datalog', *, datalog_write=True, t):
    force = None
    if force is None:
        force = problem_force_xml (path, t=t)
    if force is None:
        force = problem_force_properties (path, t=t)
    if force is None:
        force = problem_force_auto (path, t=t)
    try:
        p = problem.Problem (
            os.path.join (path, datalog),
            create=(datalog_write and force is not None),
            write=datalog_write,
            t=t
        )
    except Datalog.NotFound as error:
        raise Error ("not a problem: '%s'" % path) from error
    if p.uuid is None:
        p.create ()
    if force is None:
        force = {}
    defaults = {
        'name': lambda: os.path.basename (p.path),
        'time limit': lambda: 5.0,
        'idle limit': lambda: 10.0,
        'memory limit': lambda: 768 * 2**20,  # 768 MiB
        # TODO: more autodetect here, fix output
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

    def autodetect_generator ():
        nonlocal p, t
        # TODO:
        #    if 'generator' in problem_configuration:
        #        doall = find_source(problem_configuration['generator'])
        default = lambda: AutoGenerator (p, t=t)
        for name in ['tests', 'Tests']:
            generator = source_find (name)
            if generator is None:
                continue
            return problem.Problem.Generator (p, generator, '.', t=t)
        directory = 'source'
        if not os.path.isdir (directory):
            directory = 'src'
        if not os.path.isdir (directory):
            directory = 'tests'
        if not os.path.isdir (directory):
            return default ()
        for name in [
            'do_tests', 'doall', 'TestGen', 'TestsGen', 'genTest', 'genTests', 'Tests', 'Gen',
            'gen_tests'
        ]:
            generator = source_find (name, directory=directory)
            if generator is None:
                continue
            return problem.Problem.Generator (p, generator, directory, t=t)
        return default ()

    def autodetect_validator ():
        directory = 'source'
        if not os.path.isdir (directory):
            directory = 'src'
        if not os.path.isdir (directory):
            directory = 'tests'
        if not os.path.isdir (directory):
            return None
        for name in ['validate', 'validator']:
            validator = source_find (os.path.join (directory, name))
            if validator is None:
                continue
            return validator
        return None

    def autodetect_checker ():
        nonlocal p
        checker = None
        for name in [
            'check', 'checker', 'check_' + p.name_short,
            'checker_' + p.name_short, 'Check'
        ]:
            checker = source_find (name)
            if checker is not None:
                break
        if checker is None:
            return None
        return checker
        # TODO move into language select, as checker.java
        # if checker.name == 'Check.java':
        #     checker = "java -cp /home/burunduk3/user/include/testlib4j.jar:. " +
        #     "ru.ifmo.testlib.CheckerFramework Check"

    p.canonical (routine)
    if p.generator is None:
        p.generator = autodetect_generator ()
    if p.validator is None:
        validator = autodetect_validator ()
        if validator is not None:
            p.validator = validator
    if p.checker is None:
        p.checker = autodetect_checker ()

    return p


# === COMPILERS CONFIGURATION ==
# Здесь начинается конфигурация компиляторов. Мерзкая штука, не правда ли?

def compilers_configure ( configuration, t ):

    # script = lambda interpeter: lambda binary: Executable (binary, [interpeter])
    def script ( interpeter ):
        def result ( binary ):
            nonlocal interpeter, t
            return compilers.Executable ([interpeter, binary], t=t)
        return result

    executable_default = lambda binary: compilers.Executable.local (binary, t=t)
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
                name='c.gcc',
                t=t
            ),
            executable=executable_default,
            t=t
        ),
        'c++': L (
            binary=binary_default,
            compiler=C (
                ['g++'] + flags_cpp + ['-x', 'c++'],
                lambda source, target: ['-o', target, source],
                name='c++.gcc',
                t=t
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
                name='delphi.fpc',
                t=t
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
                name='java',
                t=t
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
                name='checker.java',
                t=t
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
                name='pascal.fpc',
                t=t
            ),
            executable=executable_default,
            t=t
        ),
    }
    set_compilers (result)

    if configuration is None:
        return result

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
    return result


