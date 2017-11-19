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

import os.path
import re
import shutil
import subprocess

import xml.etree.ElementTree as xml

from tlib import Error, Module
import compilers
from checker import Checker
from executable import Executable
from generator import Generator
from problem import Problem
from settings import Settings
from solution import Solution
from source import Source
from test import Answer, Test


class NotFoundError (Error):
    def __init__ ( self, value, *args, **kwargs ):
        super (NotFoundError, self).__init__ (*args, **kwargs)
        self._value = value

    def __str__ ( self ):
        return "not found: " + str (self._value)


class SourceNotFoundError (NotFoundError):
    def __init__ ( self, *args, **kwargs ):
        super (SourceNotFoundError, self).__init__ (*args, **kwargs)

    def __str__ ( self ):
        return "not found: source for '%s'" % str (self._value)


class TestsNotFoundError (NotFoundError):
    def __init__ ( self, *args, **kwargs ):
        super (TestsNotFoundError, self).__init__ (*args, **kwargs)

    def __str__ ( self ):
        return "not found: tests for '%s'" % str (self._value)



class Heuristics (Module):
    def __init__ ( self, *args, arguments, **kwargs ):
        super (Heuristics, self).__init__ (*args, **kwargs)
        self.__arguments = arguments
        self.__compiler_suffixes = {}
        self.__compiler_suffixes_special = {
            'py': self.__detector_python
        }
        for compiler in self._compilers.values ():
            for suffix in compiler.suffixes:
                if suffix in self.__compiler_suffixes and suffix not in self.__compiler_suffixes_special:
                    raise self._error ("confusing compiler configuration: suffix '%s' has ambiguous compiler" % suffix)
                self.__compiler_suffixes[suffix] = compiler
    
    def __parse_time ( self, value ):
        return float (value)

    def __parse_memory ( self, value ):
        for suffix, multiplier in [
            ('K', 2**10), ('M', 2**20), ('G', 2**30), ('T', 2**40),
            ('k', 2**10), ('m', 2**20), ('g', 2**30), ('t', 2**40),
            ('', 1)
        ]:
            if value.endswith(suffix):
                return int (value[0:-len (suffix)]) * multiplier
        raise self._error ("failed to parse memory: '%s'" % value)

    def __detector_python ( self, path ):
        with open (path, 'r') as f:
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

    # def __parse_file ( self, value, * ):
    #     if value in ('<std>', '<stdin>', '<stdout>'):
    #         return Problem.File.std (t=self)
    #     return Problem.File.name (value, t=self)

    def __directory_search_source ( self, path='.' ):
        for directory in ['source', 'src', 'tests']:
            if os.path.isdir (os.path.join (path, directory)):
                return directory
        else:
            raise self._error ("source directory", cls=NotFoundError)

    def __directory_search_solutions ( self, path='.' ):
        for directory in ['solutions', 'sols']:
            if os.path.isdir (os.path.join (path, directory)):
                return directory
        return '.'

    def __checker_search ( self, options ):
        for name in [
            os.path.join (options['directory-source'], 'check'),
            os.path.join (options['directory-source'], 'checker'),
            os.path.join (options['directory-source'], 'check_' + options['id']),
            os.path.join (options['directory-source'], 'checker_' + options['id']),
            os.path.join (options['directory-source'], 'Check'),
            'check',
            'checker',
            'check_' + options['id'],
            'checker_' + options['id'],
            'Check'
        ]:
            try:
        # TODO move into language select, as checker.java
        # if checker.name == 'Check.java':
        #     checker = "java -cp /home/burunduk3/user/include/testlib4j.jar:. " +
        #     "ru.ifmo.testlib.CheckerFramework Check"
                return self.__source_search (name)
            except SourceNotFoundError:
                pass
        raise self._error ('checker', cls=NotFoundError)

    def __checker_open ( self, path ):
        if path is None:
            raise self._error ("checker", cls=NotFoundError)
        try:
            source = self.__source_search (path)
            checker = self.__source_open (source, cls=Checker)
            return checker
        except SourceNotFoundError:
            pass
        if path.startswith ('testlib:'):
        #     #  if checker_name.startswith('testlib/'):
            return self.__source_open (self._configuration.testlib_checker_path (path[8:]), cls=TestlibChecker, testlib_name=path[8:])
        raise self._error ("checker '%s'" % path, cls=NotFoundError)

    def __cleaner_search ( self, options ):
        for name in ['wipe', 'clean', 'clear']:
            try:
                return self.__source_search (os.path.join (options['directory-source'], name))
            except SourceNotFoundError:
                pass
        raise self._error ('cleaner', cls=NotFoundError)

    def __garbage_search ( self, path ):
        directories = [path]
        garbage_suffixes = {'in', 'out', 'log', 'exe', 'dcu', 'ppu', 'o', 'obj', 'class', 'hi', 'manifest', 'pyc', 'pyo'}
        garbage_names = {'tests.description', 'tests.gen', 'input', 'output'}
        for directory in directories:
            for filename in map (lambda file: os.path.join (directory, file), os.listdir (directory)):
                if os.path.isdir (filename):
                    directories.append (filename)
                    continue
                nonse, suffix = os.path.splitext (filename)
                if suffix:
                    suffix = suffix[1:]
                if suffix in garbage_suffixes or filename in garbage_names:
                    yield filename

    def __source_search_all ( self, path ):
        directories = [path]
        for directory in directories:
            for filename in map (lambda file: os.path.join (directory, file), os.listdir (directory)):
                if os.path.isdir (filename):
                    directories.append (filename)
                    continue
                nonse, suffix = os.path.splitext (filename)
                if suffix:
                    suffix = suffix[1:]
                if suffix in self.__compiler_suffixes.keys ():
                    yield filename

    def __source_search ( self, path ):
        """
            function for location source file with unknown sufix (<path>.*)
            available suffixes depend on available languages
            throws SourceNotFoundError if nothing found
        """
        for filename in [path + '.' + suffix for suffix in self.__compiler_suffixes.keys ()] + [path]:
            if not os.path.isfile (filename):
                continue
            return filename
        raise self._error (path, cls=SourceNotFoundError)

    def __source_open ( self, path, *args, cls=Source, run_in_directory=False, **kwargs ):
        if isinstance (path, (Source, Executable)):
            return path
        suffix = path.split ('.')[-1]
        try:
            detector = self.__compiler_suffixes_special[suffix]
        except KeyError:
            detector = lambda path: self.__compiler_suffixes [suffix]
        try:
            compiler = detector (path)
        except KeyError:
            raise self._error ("unknown source: '%s'" % path)
        if run_in_directory:
            source = cls (os.path.basename (path), compiler, *args, t=self, directory=os.path.dirname (path), **kwargs)
        else:
            source = cls (os.path.abspath (path), compiler, *args, t=self, name=path, **kwargs)
        binary = compiler.binary (source)
        if os.path.isfile (binary) and os.stat (binary).st_mtime >= os.stat (source.path).st_mtime:
            source.executable = compiler.executable (binary, source)
        return source

    def __problem_properties_parse ( self, path ):
        with open (path, 'r') as f:
            for line in f.readlines ():
                if line:
                    line = line.split ('#') [0]
                line = line.strip ()
                if not line:
                    continue
                try:
                    key, value = [token.strip() for token in line.split('=', 1)]
                except ValueError:
                    t._log ("problem.properties: bad line '%s'" % line)
                    continue
                if value[0] == '"' and value[-1] == '"':
                    value = value[1:-1]
                yield key, value

    def __problem_open_xml ( self, path ):
        """open polygon-style problem with properties in problem.xml"""
        try:
            with open (os.path.join (path, 'problem.xml'), 'r') as f:
                data = f.read ()
        except FileNotFoundError:
            raise self._error ("problem.xml", cls=NotFoundError) from None
        data = xml.XML (data)
        if list (sorted (data.attrib.keys ())) == ['id', 'version'] and data.attrib['version'] == "1.0":
            self._log.info ("ignore problem.xml: not problem data but config for PCMS2")
            raise self._error ("problem.xml", cls=NotFoundError) from None
        print (data.tag, data.text, data.attrib)
        raise NotImplementedError ("Heuristics.__problem_open_xml")

    def __problem_open_properties ( self, path ):
        """NEERC-style problem with properties in problem.properties"""
        try:
            return {k:v for k, v in self.__problem_properties_parse (os.path.join (path, 'problem.properties'))}
        except FileNotFoundError:
            raise self._error ("problem.properties", cls=NotFoundError) from None

    def __problem_open_gassa ( self, path ):
        """problem with tools.sh, problem.sh and many scripts made by Gassa commonly in SPbSU archives"""
        directory_source = self.__directory_search_source (path)
        problem_sh = os.path.join (directory_source, 'problem.sh')
        if not os.path.isfile (problem_sh):
            raise self._error ("problem.sh", cls=NotFoundError) from None
        bash = Executable (['bash'], source=None, path=None, t=self)
        def option ( name ):
            nonlocal bash, directory_source
            result = bash.run (['-c', ". problem.sh && echo \"${%s}\"" % name], directory=directory_source, stdout=subprocess.PIPE)
            data = result.stdout.strip ()
            if not data:
                return None
            return data
        options_gassa = {
            key: value for key, value in map (lambda key: (key, option (key)),
            [
                'IO_FILES', 'USE_GRADERS', 'PROBLEM', 'AUTHOR', 'SUFFIX', 'LANGUAGE', 'SOLUTION',
                'GENERATOR', 'VALIDATOR', 'CHECKER', 'TEST_PATTERN', 'DO_CHECK', 'DO_CLEAN',
                'CUSTOM_WIPE'
            ]) if value is not None
        }
        options = {
            key: os.path.normpath (os.path.join (directory_source, options_gassa[keyg])) for key, keyg in [
                ('solution', 'SOLUTION'),
                # ('generator', 'GENERATOR'), # generator is unusual: places tests in src/
                ('validator', 'VALIDATOR'),
                ('checker', 'CHECKER'),
            ] if keyg in options_gassa
        }
        options['generator'] = os.path.join (directory_source, 'doall.sh')
        if 'PROBLEM' in options_gassa:
            options['id'] = options_gassa['PROBLEM']
        if 'IO_FILES' in options_gassa and options_gassa['IO_FILES'] == 'true':
            options['input-file'] = options['id'] + '.in'
            options['output-file'] = options['id'] + '.out'
        # TODO: use test mask
        return options

    def __problem_open_makefile ( self, path ):
        """problem with makefiles, likely from pkun"""
        options = {
            'generator': Executable (['make'], source=None, path=None, t=self),
            'cleaner': Executable (['make', 'clean'], source=None, path=None, t=self)
        }
        options_pkun_legacy = {}
        grep = Executable (['grep'], source=None, path=None, t=self)
        result = grep.run (['--', ':=', 'makefile'], directory=path, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        # self._log.debug ("__problem_open_makefile ", result)
        if not result:
            raise self._error ("makefile", cls=NotFoundError)
        for line in result.stdout.split ('\n'):
            if ':=' not in line:
                continue
            key, value = line.split (':=', 1)
            options_pkun_legacy[key.strip ()] = value.strip ()
        try:
            directory_source = self.__directory_search_source ()
            self.__interactor_search ({'directory-source': directory_source})
            interactive = True
        except NotFoundError:
            interactive = False
        if 'InputFileName' in options_pkun_legacy:
            options['input-file'] = options_pkun_legacy['InputFileName']
        if 'OutputFileName' in options_pkun_legacy:
            options['output-file'] = options_pkun_legacy['OutputFileName']

        make = Executable (['make'], source=None, path=None, t=self)
        result = make.run (['problemInfo'], directory=path, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if not result:
            raise self._error ("makefile", cls=NotFoundError)
        options_pkun = {}
        for line in result.stdout.split ('\n'):
            if ':' not in line or '=' not in line:
                continue
            nonse, info = line.split (':', 1)
            key, value = info.split ('=', 1)
            options_pkun[key.strip ()] = value.strip ()
        if '$(problem)' in options_pkun:
            options['id'] = options_pkun['$(problem)']
        if '$(mainSuffix)' in options_pkun: # I'd like to use $(mainSrc), but it has useless comment after value
            options['solution-token'] = options_pkun['$(mainSuffix)']
        # TODO: use $(TestMask)
        if not interactive:
            if 'input-file' not in options:
                options['input-file'] = options['id'] + '.in'
            if 'output-file' not in options:
                options['output-file'] = options['id'] + '.out'
        return options

    def __problem_open_auto ( self, path ):
        """anarchy-style problem: try to guess properties"""
        try:
            self.__directory_search_source (path)
        except NotFoundError:
            return None  # no file, no problems
        return {}  # correct problem but we don't know anything about it

    def __generator_search ( self, options ):
        for name in ['tests', 'Tests']:
            try:
                return self.__source_search (name)
            except SourceNotFoundError:
                pass
        directory = options['directory-source']
        for name in [
            'do_tests', 'doall', 'TestGen', 'TestsGen', 'genTest', 'genTests', 'Tests', 'Gen',
            'gen_tests'
        ]:
            try:
                return self.__source_search (os.path.join (directory, name))
            except SourceNotFoundError:
                pass
        return None

    def __generator_open ( self, path, *, problem, **kwargs ):
        generator = self.__source_open (path, run_in_directory=True)
        return Generator.external (generator, heuristics=self, **kwargs, t=self, problem=problem)

    def __generator_default ( self, path ):
        # TODO:
        # default = lambda: AutoGenerator (p, t=t)
        # print ("[debug] autodetect_generator ()", file=sys.stderr)
        # TODO: convert_tests(tests), move to generation, for copy
        #    return self.__generator_default (path)
        raise NotImplementedError ("%s.__generator_default" % type (self))

    def __validator_search ( self, options ):
        directory = options['directory-source']
        for path in [
            os.path.join (directory, 'validate'),
            os.path.join (directory, 'validator'),
            'validate',
            'validator'
        ]:
            try:
                return self.__source_search (path)
            except SourceNotFoundError:
                pass
        raise self._error ("validator", cls=NotFoundError)

    def __validator_open ( self, path, *, problem ):
        return self.__source_open (path)

    def __interactor_search ( self, options ):
        directory = options['directory-source']
        for path in [
            os.path.join (directory, 'iserver'),
            os.path.join (directory, 'Interact'),
            'iserver',
            'Interact'
        ]:
            try:
                return self.__source_search (path)
            except SourceNotFoundError:
                pass
        raise self._error ("interactor", cls=NotFoundError)

    def __solution_search ( self, options, token=None ):
        """    
            function for location solution with given token (options['solution-token'])
        """
        if token is None:
            token = options['solution-token']
        directory = options['directory-solutions']
        for path in [
            os.path.join (directory, token),
            os.path.join (directory, options['id'] + '_' + token),
            token,
            options['id'] + '_' + token,
        ]:
            try:
                return self.__source_search (path)
            except SourceNotFoundError:
                pass
        raise NotImplementedError ("%s.solution_search" % type (self))

    def problem_search ( self, path='.' ):
        """
            function for dive into directory tree
            @param path directory to start from
            yields all subdirectories which look like problems
        """
        queue = [path]
        for path in queue:
            if not os.path.isdir (path):
                continue
            options = self.problem_preopen (path)
            # self._log.debug (path, options=)
            if options is not None:
                yield self.problem_open (path, options_raw=options)
            else:
                queue += [os.path.join (path, x) for x in sorted (os.listdir (path))]


    def problem_preopen ( self, path ):
        for opener in [
            self.__problem_open_xml,
            self.__problem_open_gassa,
            self.__problem_open_makefile,
            self.__problem_open_properties,
            self.__problem_open_auto
        ]:
            try:
                return opener (path)
            except NotFoundError:
                pass
        raise self._error ("problem in '%s'" % path, cls=NotFoundError)

    def problem_open ( self, path='.', *, options_raw=None ):
        if options_raw is None:
            options_raw = self.problem_preopen (path)
        if options_raw is None:
            if path == '.':
                path = os.path.split (os.path.abspath ('.'))[-1]
            raise self._error ("not a problem: '%s'" % path)
        path_old = os.getcwd ()
        path_canonical = os.path.abspath (path)
        try:
            os.chdir (path)
    
            options = {}
            options_ok = {'solution-token'}
            options_defaults = {}
    
            for key, target, default in [
                ('id', options_raw, lambda: os.path.basename (os.path.abspath (path))),
                ('id', options, lambda: options_raw['id']),
                ('directory-source', options_raw, lambda: self.__directory_search_source ()),
                ('directory-solutions', options_raw, lambda: self.__directory_search_solutions ()),
                ('directory-temp', options_raw, lambda: '.temp'),
                ('directory-tests', options_raw, lambda: 'tests'),
    #         # if 'tests-directory' not in configuration:
    #         #    configuration.update({'tests-directory': os.path.join(path, 'tests')})
                ('checker', options_raw, lambda: self.__arguments.checker),
                # TODO check from arguments is forced
                ('generator', options_raw, lambda: self.__generator_search (options_raw)),
                ('validator', options_raw, lambda: self.__validator_search (options_raw)),
                ('interactor', options_raw, lambda: self.__interactor_search (options_raw)),
                ('checker', options_raw, lambda: self.__checker_search (options_raw)),
                ('cleaner', options_raw, lambda: self.__cleaner_search (options_raw)),
                ('time-limit', options_raw, lambda: self._log.notice ('time limit not set')),
                ('idle-limit', options_raw, lambda: self._log.notice ('idle limit not set')),
                ('memory-limit', options_raw, lambda: self._log.notice ('memory limit not set')),
                # ('input-file', options_raw, lambda: self._log.notice ('input file not set')),
                # ('output-file', options_raw, lambda: self._log.notice ('output not set')),
                ('input-file', options_raw, lambda: options_raw['id'] + '.in'),
                ('output-file', options_raw, lambda: options_raw['id'] + '.out'),
                ('solution', options_raw, lambda: self.__solution_search (options_raw)),
                ('limit_time', options_defaults, lambda: self.__parse_time (options_raw['time-limit'])),
                ('limit_idle', options_defaults, lambda: self.__parse_time (options_raw['idle-limit'])),
                ('limit_memory', options_defaults, lambda: self.__parse_memory (options_raw['memory-limit'])),
                ('filename_input', options_defaults, lambda: options_raw['input-file']),
                ('filename_output', options_defaults, lambda: options_raw['output-file']),
                ('directory_source', options, lambda: options_raw['directory-source']),
                ('directory_temp', options, lambda: options_raw['directory-temp']),
                ('directory_tests', options, lambda: options_raw['directory-tests']),
            ]:
                options_ok.add (key)
                if key in target:
                    continue
                try:
                    value = default ()
                except KeyError:
                    continue
                except NotFoundError:
                    continue
                if value is not None:
                    target[key] = value
    
            defaults = Settings (self._t.defaults, **options_defaults)
            problem = Problem (
                path_canonical,
                **options,
                defaults=defaults,
                sources=[self.__source_open (x) for x in self.__source_search_all ('.')],
                garbage=[x for x in self.__garbage_search ('.')],
                t=self._t
            )
            if 'generator' in options_raw:
                options_ok.add ('generator')
                problem.generator = self.__generator_open (options_raw['generator'], directory_tests=options_raw['directory-tests'], problem=problem)
            if 'validator' in options_raw:
                options_ok.add ('validator')
                problem.validator = self.__validator_open (options_raw['validator'], problem=problem)
            if 'interactor' in options_raw:
                options_ok.add ('interactor')
                problem.interactor = self.__source_open (options_raw['interactor'])
            if 'checker' in options_raw:
                options_ok.add ('checker')
                problem.checker = self.__checker_open (options_raw['checker'])
            if 'cleaner' in options_raw:
                options_ok.add ('cleaner')
                problem.cleaner = self.__source_open (options_raw['cleaner'], run_in_directory=True)
            if 'solution' in options_raw:
                options_ok.add ('solution')
                problem.solution_model = self.solution_open (options_raw['solution'], problem=problem)
            try:
                if problem.generator is not None:
                    problem.tests = problem.generator.tests ()
            except TestsNotFoundError:
                pass
            
            for key in options_raw.keys ():
                if key in options_ok:
                    continue
                self._log.warning ("ignored option: %s" % key)
        
            return problem
        finally:
            os.chdir (path_old)

    def defaults ( self, *args, **kwargs ):
        return Settings (
            *args,
            limit_time = None if self.__arguments.limit_time is None else self.__parse_time (self.__arguments.limit_time),
            limit_idle = None if self.__arguments.limit_idle is None else self.__parse_time (self.__arguments.limit_idle),
            limit_memory = None if self.__arguments.limit_memory is None else self.__parse_memory (self.__arguments.limit_memory),
            filename_input = None if self.__arguments.filename_input is None else self.__arguments.filename_input,
            filename_output = None if self.__arguments.filename_output is None else self.__arguments.filename_output,
            **kwargs
        )

    def solution_open ( self, path, *args, **kwargs ):
        solution = self.__source_search (path)
        return self.__source_open (solution, *args, cls=Solution, **kwargs)

    def tests_search ( self, directory, problem ):
        tests = []
        try:
            files = sorted (os.listdir (directory))
        except FileNotFoundError: # no directory, no tests
            raise self._error (problem, cls=TestsNotFoundError) from None
        for filename in files:
            if not re.match ('^\d{2,3}$', filename):
                continue
            if not os.path.isfile (os.path.join (directory, filename)):
                continue
            test = Test (os.path.join (directory, filename))
            if os.path.isfile (os.path.join (directory, filename + '.a')):
                test.answer = Answer (os.path.join (directory, filename + '.a'), test)
            tests.append (test)
        if not tests:
            raise self._error (problem, cls=TestsNotFoundError)
        return tests


class TestlibChecker (Checker):
    def __init__ ( self, *args, testlib_name, **kwargs ):
        super (TestlibChecker, self).__init__ (*args, **kwargs)
        self.__name = testlib_name

    def __str__ ( self ):
        return "testlib's %s" % self.__name


#
#  Path stone with no way beyond, hello there, stranger, how are you?
#
# FORCED OPTIONS
#



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

# class AutoGenerator (Type):
#     LEV = 'problem.generator.auto'
# 
#     def __init__ ( self, problem, *, t ):
#         super (AutoGenerator, self).__init__ (t=t)
#         self.__problem = problem
# 
#     def __str__ ( self ):
#         return '<generator:automatic>'
# 
#     def __eq__ ( self, x ):
#         return type (self) is type (x)
# 
#     def commit ( self ):
#         return (AutoGenerator.LEV,)
# 
#     def run ( self ):
#         directory = 'source'
#         if not os.path.isdir (directory):
#             directory = 'src'
#         if not os.path.isdir (directory):
#             directory = 'tests'
#         if not os.path.isdir (directory):
#             raise Error ('[problem %s]: failed to find source directory' % self.__problem.name)
#         count_hand, count_gen, failure = 0, 0, False
#         # TODO: this is slow on some outdated systems
#         for test in ['%02d' % i for i in range (100)]:
#             target = os.path.join ('.tests', '%d' % (count_hand + count_gen))
#             for f in [os.path.join (directory, test + suffix) for suffix in ['.hand', '.manual']]:
#                 if not os.path.isfile (f):
#                     continue
#                 shutil.copy (f, target)
#                 count_hand += 1
#                 break
#             else:
#                 generator = source_find ('do' + test)
#                 if generator is None:
#                     generator = source_find ('gen' + test)
#                 if generator is None:
#                     continue
#                 result = generator.run (stdout=open (target, 'w'))
#                 if not result:
#                     raise Error ('generator (%s) failed' % generator)
#                     failure = True
#                 else:
#                     count_gen += 1
#         if count_hand != 0:
#             self._log ('manual tests copied: %d' % count_hand)
#         if count_gen != 0:
#             self._log ('generated tests: %d' % count_gen)
#         return not failure
# 
#     @classmethod
#     def set ( cls, problem, *, t ):
#         return cls (problem, t=t)
# 
#     @classmethod
#     def register ( cls, *, t ):
#         t.register_problem_upgrade (
#             problem.Problem.TYPE_GENERATOR,
#             AutoGenerator.LEV,
#             lambda problem, data, cls=cls, t=t: cls.set (problem, t=t)
#         )
    # FILE, GENERATOR = range (2)
    # def __init__ ( self, problem=None, path=None, generator=None, name=None ):
        # self.__problem = problem
        # self.__name = name
        # if self.__name is None:
        #     self.__name = self.__path
        # if self.__name is None:
        #     self.__name = '<unknown>'
        # if generator is not None:
        #     self.__type = Test.GENERATOR
        #     self.__generator = generator
        # elif path is not None:
        #     self.__type = Test.FILE
        # else:
        #     raise Exception ("failed to create test: unknown type")
#     def __str__ ( self ):
#         return self.__name
# 
#     def create ( self ):
#         return {
#             Test.FILE: lambda: self.__path,
#             Test.GENERATOR: lambda: self.__create_generate ()
#         } [self.__type] ()
# 
#     def __create_generate ( self ):
#         Error.ensure (self.__type is Test.GENERATOR)
#         path = '.temp/00' if self.__path is None else self.__path
#         result = self.__generator.run (stdout=open(path, 'w'))
#         # TODO: validate test
#         testset_answers (self.__problem, tests=[path], force=True, quiet=True)
#         if not result:
#             raise Error ('generator (%s) failed' % self.__generator)
#             return None
#         return path
# 
#     @classmethod
#     def file ( self, path, problem=None, name=None ):
#         return Test (problem, path=path, name=name)
# 
#     @classmethod
#     def generate ( self, generator, problem=None, name=None ):
#         return Test (problem, generator=generator, name=name)


# === COMPILERS CONFIGURATION ==
# Здесь начинается конфигурация компиляторов. Мерзкая штука, не правда ли?

class Configuration (Module):
    def __init__ ( self, testlib_checker_path=None, *args, **kwargs ):
        super (Configuration, self).__init__ (*args, **kwargs)
        self.__testlib_checker_path = testlib_checker_path
        self.__compilers = {}
        self.__configure_compilers ()
    
    testlib_checker_path = property (lambda self: self.__testlib_checker_path)
    compilers = property (lambda self: self.__compilers)

    def __compiler_register ( self, compiler ):
        self.__compilers[compiler.name] = compiler

    def __configure_compilers ( self ):
        # include_path = '/home/burunduk3/user/include/testlib.ifmo'
        include_path = '/home/burunduk3/user/include'
        compile_c = Executable (['gcc', '-Wall', '-Wextra', '-D__T_SH__', '-lm', '-I', include_path] + os.environ.get ('CFLAGS', '').split () + ['-Wno-error'], source=None, path=None, t=self)
        compile_cpp = Executable (['g++', '-Wall', '-Wextra', '-D__T_SH__', '-lm', '-I', include_path] + os.environ.get ('CXXFLAGS', '').split () + ['-Wno-error'], source=None, path=None, t=self)
        compile_delphi = Executable (['fpc', '-Mdelphi', '-O3', '-FE.', '-v0ewn', '-Sd', '-Fu' + include_path, '-Fi' + include_path, '-d__T_SH__'], source=None, path=None, t=self)
        compile_dmd = Executable (['dmd', '-O', '-wi', '-od.'], source=None, path=None, t=self)
        compile_fpc = Executable (['fpc', '-O3', '-FE.', '-v0ewn', '-Sd', '-Fu' + include_path, '-Fi' + include_path, '-d__T_SH__'], source=None, path=None, t=self)
        compile_java = Executable (['javac'], source=None, path=None, t=self)
        java_cp_suffix = os.environ.get ('CLASSPATH', None)
        if java_cp_suffix is None:
            java_cp_suffix = ""
        else:
            java_cp_suffix = ":" + java_cp_suffix

        suffix_remove = lambda source: os.path.splitext (source.path)[0]
        def executable_binary ( path, source ):
            nonlocal self
            if path[0] != '/':
                path = os.path.join ('.', path)
            return Executable ([path], source, path=path, t=self)
        def executable_java ( path, source ):
            nonlocal self, java_cp_suffix
            return Executable (['java', '-Xms8M', '-Xmx128M', '-Xss64M', '-ea', '-cp', os.path.dirname (path) + java_cp_suffix, os.path.splitext (os.path.basename (path))[0]], source, path=path, t=self)
        def executable_java_checker ( path, source ):
            nonlocal self, java_cp_suffix
            return Executable (['java', '-Xms8M', '-Xmx128M', '-Xss64M', '-ea', '-cp', os.path.dirname (path) + java_cp_suffix, 'ru.ifmo.testlib.CheckerFramework', os.path.splitext (os.path.basename (path))[0]], source, path=path, t=self)
        script = lambda n, s: compilers.Compiler (n, suffixes=s, executable=lambda path, source: Executable ([n, path], source, path=path, t=self), t=self)
        
        for compiler in [
            script ('bash', ['sh']),
            script ('perl', ['pl']),
            script ('python2', []),
            script ('python3', []),
            compilers.Compiler (
                name='c.gcc', suffixes=['c'],
                binary=suffix_remove,
                compile=lambda source, binary: (compile_c, ['-o', binary, '-x', 'c', source.path]),
                executable=executable_binary,
                t=self
            ),
       #'c++': 'c++', 'C': 'c++', 'cxx': 'c++', 'cpp': 'c++',
            compilers.Compiler (
                name='c++.gcc', suffixes=['c++', 'C', 'cc', 'cxx', 'cpp'],
                binary=suffix_remove,
                compile=lambda source, binary: (compile_cpp, ['-o', binary, '-x', 'c++', '-std=c++17', source.path]),
                executable=executable_binary,
                t=self
            ),
            compilers.Compiler (
                name='delphi.fpc', suffixes=['dpr'],
                binary=suffix_remove,
                compile=lambda source, binary: (compile_delphi, ['-o' + binary, source.path]),
                executable=executable_binary,
                t=self
            ),
            compilers.Compiler (
                name='pascal.fpc', suffixes=['pas'],
                binary=suffix_remove,
                compile=lambda source, binary: (compile_fpc, ['-o' + binary, source.path]),
                executable=executable_binary,
                t=self
            ),
            compilers.Compiler (
                name='dmd', suffixes=['d'],
                binary=suffix_remove,
                compile=lambda source, binary: (compile_dmd, ['-of' + binary, source.path]),
                executable=executable_binary,
                t=self
            ),
            compilers.Compiler (
                name='java', suffixes=['java'],
                binary = lambda source: os.path.splitext (source.path)[0] + '.class',
                compile=lambda source, target: (compile_java, ['-cp', os.path.dirname (source.path), source.path]),
                executable=executable_java,
                t=self
            ),
            compilers.Compiler (
                name='java.checker', suffixes=[],
                binary = lambda source: os.path.splitext (source.path)[0] + '.class',
                compile=lambda source, target: (compile_java, ['-cp', os.path.dirname (source.path), source.path]),
                executable=executable_java_checker,
                t=self
            ),
        ]:
            self.__compiler_register (compiler)


