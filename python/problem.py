import itertools
import os
import os.path
import random
import re
import shutil
import struct

import common as t
from datalog import Datalog, Type
import heuristic

class Problem (Datalog):
    LEV_CREATE = 'problem.create'
    LEV_NAME_SHORT = 'problem.name_short'
    LEV_LIMIT_TIME = 'problem.limit_time'
    LEV_LIMIT_IDLE = 'problem.limit_idle'
    LEV_LIMIT_MEMORY = 'problem.limit_memory'
    LEV_INPUT = 'problem.input'
    LEV_INPUT_STD = 'problem.input.std'
    LEV_OUTPUT = 'problem.output'
    LEV_OUTPUT_STD = 'problem.output.std'
    LEV_CHECKER = 'problem.checker'
    LEV_SOLUTION = 'problem.solution'
    LEV_GENERATOR_AUTO = 'problem.generator.auto'
    LEV_GENERATOR_EXT = 'problem.generator.external'
    LEV_VALIDATOR = 'problem.validator'


    class File (Type):
        class Std (Type):
            def __str__ ( self ):
                return '<std>'
            def __eq__ ( self, x ):
                return type (self) is type (x)

        class Name (Type):
            def __init__ ( self, name ):
                self.__name = name
            def __str__ ( self ):
                return self.__name
            def __eq__ ( self, x ):
                if type (self) is not type (x):
                    return False
                return self.__name == x.__name

        @classmethod
        def std ( cls ):
            return Problem.File.Std ()
        @classmethod
        def name ( cls, name ):
            return Problem.File.Name (name)

    class Generator (Type):
        class Auto (Type):
            def __init__ ( self, problem ):
                self.__problem = problem
            def __str__ ( self ):
                return '<automatic>'
            def __eq__ ( self, x ):
                return type (self) is type (x)
            def run ( self ):
                return self.__problem.autogenerate ()
        class External (Type):
            def __init__ ( self, problem, source, directory ):
                self.__problem = problem
                self.__source = source
                self.__directory = directory
            def __str__ ( self ):
                return str (self.__source)
            def __eq__ ( self, x ):
                if type (self) is not type (x):
                    return False
                return self.__source == x.__source
            def run ( self ):
                r = self.__source.run (directory=self.__directory)
                if not r:
                    raise t.Error ('generator failed: %s' % self)
                return self.__problem.autofind_tests (self.__directory)
        
        @classmethod
        def auto ( cls, problem ):
            return Problem.Generator.Auto (problem)
        @classmethod
        def external ( cls, problem, source, directory ):
            return Problem.Generator.External (problem, source, directory)


    def __init__ ( self, datalog, *, create=False, t ):
        self.__path = os.path.dirname (os.path.abspath (datalog))
        self.__uuid = None
        self.__name_short = None
        self.__limit_time = None
        self.__limit_idle = None
        self.__limit_memory = None
        self.__input = None
        self.__output = None
        self.__solution = None
        self.__generator = None
        self.__validator = None
        self.__checker = None
        super (Problem, self).__init__ (datalog, actions={
            Problem.LEV_CREATE: lambda uuid: self.__lev_create (uuid)
        }, create=create, t=t)
        self.__tests = None

    def __lev_create ( self, uuid ):
        self.__uuid = uuid
        self._actions = {
            Problem.LEV_NAME_SHORT: lambda value: self.__lev_name_short (value),
            Problem.LEV_LIMIT_TIME: lambda value: self.__lev_limit_time (value),
            Problem.LEV_LIMIT_IDLE: lambda value: self.__lev_limit_idle (value),
            Problem.LEV_LIMIT_MEMORY: lambda value: self.__lev_limit_memory (value),
            Problem.LEV_INPUT: lambda value: self.__lev_input_name (value),
            Problem.LEV_INPUT_STD: lambda: self.__lev_input_std (),
            Problem.LEV_OUTPUT: lambda value: self.__lev_output_name (value),
            Problem.LEV_OUTPUT_STD: lambda: self.__lev_output_std (),
            Problem.LEV_CHECKER: lambda path, compiler: self.__lev_checker (path, compiler),
            Problem.LEV_SOLUTION: lambda path, compiler: self.__lev_solution (path, compiler),
            Problem.LEV_GENERATOR_AUTO: lambda: self.__lev_generator_auto (),
            Problem.LEV_GENERATOR_EXT: lambda path, compiler, directory: \
                self.__lev_generator_external (path, compiler, directory),
            Problem.LEV_VALIDATOR: lambda path, compiler: self.__lev_validator (path, compiler)
        }
        return uuid
    def __lev_name_short ( self, value ):
        self.__name_short = value
        return True
    def __lev_limit_time ( self, value ):
        self.__limit_time = float (value)
        return True
    def __lev_limit_idle ( self, value ):
        self.__limit_idle = float (value)
        return True
    def __lev_limit_memory ( self, value ):
        self.__limit_memory = int (value)
        return True
    def __lev_input_std ( self ):
        self.__input = Problem.File.std ()
        return True
    def __lev_input_name ( self, value ):
        self.__input = Problem.File.name (value)
        return True
    def __lev_output_std ( self ):
        self.__output = Problem.File.std ()
        return True
    def __lev_output_name ( self, value ):
        self.__output = Problem.File.name (value)
        return True
    def __lev_checker ( self, path, compiler ):
        self.__checker = heuristic.Source (path, compiler)
        return True
    def __lev_solution ( self, path, compiler ):
        self.__solution = heuristic.Source (path, compiler) # TODO: move Source outside of heuristic
        return True
    def __lev_generator_auto ( self ):
        self.__generator = Problem.Generator.auto (self)
        return True
    def __lev_generator_external ( self, path, compiler, directory ):
        self.__generator = Problem.Generator.external (
            self, heuristic.Source (path, compiler), directory
        )
        return True
    def __lev_validator ( self, path, compiler ):
        self.__validator = heuristic.Source (path, compiler)
        return True

    def create ( self, uuid=None ):
        if uuid is None:
            uuid = ''.join (['%x' % random.randint (0, 15) for x in range (32)])
        return self._commit (Problem.LEV_CREATE, uuid)

    path = property (lambda self: self.__path)
    uuid = property (lambda self: self.__uuid)
    def __set_name_short ( self, value ):
        return self._commit (Problem.LEV_NAME_SHORT, str (value))
    name_short = property (lambda self: self.__name_short, __set_name_short)
    def __set_limit_time ( self, value ):
        return self._commit (Problem.LEV_LIMIT_TIME, '%.20f' % float (value)) # TODO: exact pack
    limit_time = property (lambda self: self.__limit_time, __set_limit_time)
    def __set_limit_idle ( self, value ):
        return self._commit (Problem.LEV_LIMIT_IDLE, '%.20f' % float (value)) # TODO: exact pack
    limit_idle = property (lambda self: self.__limit_idle, __set_limit_idle)
    def __set_limit_memory ( self, value ):
        return self._commit (Problem.LEV_LIMIT_MEMORY, '%d' % int (value))
    limit_memory = property (lambda self: self.__limit_memory, __set_limit_memory)
    def __set_input_std ( self ):
        return self._commit (Problem.LEV_INPUT_STD)
    def __set_input_name ( self, value ):
        return self._commit (Problem.LEV_INPUT, value)
    def __set_input ( self, value ):
        if type (value) is Problem.File.Std:
            return self.__set_input_std ()
        if type (value) is Problem.File.Name:
            return self.__set_input_name (str (value))
        assert False
    input = property (lambda self: self.__input, __set_input)
    def __set_output_std ( self ):
        return self._commit (Problem.LEV_OUTPUT_STD)
    def __set_output_name ( self, value ):
        return self._commit (Problem.LEV_OUTPUT, value)
    def __set_output ( self, value ):
        if type (value) is Problem.File.Std:
            return self.__set_output_std ()
        if type (value) is Problem.File.Name:
            return self.__set_output_name (str (value))
        assert False
    output = property (lambda self: self.__output, __set_output)
    def __set_checker ( self, value ):
        return self._commit (Problem.LEV_CHECKER, value.path, value.compiler)
    checker = property (lambda self: self.__checker, __set_checker)
    def __set_solution ( self, value ):
        return self._commit (Problem.LEV_SOLUTION, value.path, value.compiler)
    solution = property (lambda self: self.__solution, __set_solution)
    def __set_generator_auto ( self ):
        return self._commit (Problem.LEV_GENERATOR_AUTO)
    def __set_generator_external ( self, value, directory ):
        return self._commit (Problem.LEV_GENERATOR_EXT, value.path, value.compiler, directory )
    generator = property (lambda self: self.__generator)
    def __set_validator ( self, value ):
        return self._commit (Problem.LEV_VALIDATOR, value.path, value.compiler)
    validator = property (lambda self: self.__validator, __set_validator)

    name = property (lambda self: self.__name_short if self.__name_short is not None else self.__uuid)
    tests = property (lambda self: self.__tests)

    def __parse_memory ( self, value ):
        for suffix, multiplier in [('K', 2**10), ('M', 2**20), ('G', 2**30), ('T', 2**40), ('', 1)]:
            if value.endswith(suffix):
                return int(value.replace(suffix, '')) * multiplier
        assert False
    def __parse_file ( self, value ):
        if value in ('<std>', '<stdin>', '<stdout>'):
            return Problem.File.std ()
        return Problem.File.name (value)
    def __parse_problem_properties ( self, filename ):
        with open (filename) as x:
            for line in x:
                key, value = [token.strip() for token in line.split('=', 1)]
                if value[0] == '"' and value[-1] == '"':
                    value = value[1:-1]
                yield key, value
    def __find_solution ( self, token ):
        result = heuristic.Source.find (token)
        if result is not None:
            return result
        result = heuristic.Source.find (self.__name_short + '_' + token)
        if result is not None:
            return result
        return None

    def __autodetect_generator ( self ):
        # TODO:
        #    if 'generator' in problem_configuration:
        #        doall = find_source(problem_configuration['generator'])
        default = lambda: self.__set_generator_auto ()
        for name in ['tests', 'Tests']:
            generator = heuristic.Source.find (name)
            if generator is None:
                continue
            return self.__set_generator_external (generator, '.')
        directory = 'source'
        if not os.path.isdir (directory):
            directory = 'tests'
        # self._t.log.debug ('directory: "%s"' % directory)
        if not os.path.isdir (directory):
            return default ()
        for name in ['do_tests', 'doall', 'TestGen', 'TestsGen', 'genTest', 'genTests', 'Tests', 'Gen', 'gen_tests']:
            # self._t.log.debug ('source: "%s"' % os.path.join (directory, name))
            generator = heuristic.Source.find (os.path.join (directory, name))
            if generator is None:
                continue
            return self.__set_generator_external (generator, directory)
        return default ()

    def __autodetect_validator ( self ):
        directory = 'source'
        if not os.path.isdir (directory):
            directory = 'tests'
        if not os.path.isdir (directory):
            return None
        for name in ['validate', 'validator']:
            validator = heuristic.Source.find (os.path.join (directory, name))
            if validator is None:
                continue
            return self.__set_validator (validator)
        return None
    def __autodetect_checker ( self ):
        checker = None
        for name in ['check', 'checker', 'check_' + self.__name_short, 'checker_' + self.__name_short, 'Check']:
            checker = heuristic.Source.find (name)
            if checker is not None:
                break
        if checker is None:
            return None
        return self.__set_checker (checker)
  # if checker.name == 'Check.java':
  #     checker = "java -cp /home/burunduk3/user/include/testlib4j.jar:. ru.ifmo.testlib.CheckerFramework Check"

    def reconfigure ( self ):
        os.chdir (self.__path)
        defaults = [
            ('name', lambda: self.name_short, lambda: self.__set_name_short (os.path.basename (self.__path))),
            ('input', lambda: self.input, lambda: self.__set_input_std ()),
            ('output', lambda: self.output, lambda: self.__set_output_std ()),
            ('time limit', lambda: self.limit_time, lambda: self.__set_limit_time (5.0)),
            ('idle limit', lambda: self.limit_idle, lambda: self.__set_limit_idle (10.0)),
            ('memory limit', lambda: self.limit_memory, lambda: self.__set_limit_memory (768 * 2**20)), # 768 MiB
        ]
        for name, key, setter in defaults:
            if key () is not None:
                continue
            setter ()
            self._t.log.warning ("%s isn't set for problem '%s', use default (%s)" % (
                name, self.name_short if self.name_short is not None else self.uuid, key ()
            ))
        pp_file = 'problem.properties'
        if os.path.isfile (pp_file):
            pp_morph = {
                'time-limit': (lambda: self.limit_time, self.__set_limit_time, lambda x: float (x)),
                'idle-limit': (lambda: self.limit_idle, self.__set_limit_idle, lambda x: float (x)),
                'memory-limit': (lambda: self.limit_memory, self.__set_limit_memory, lambda x: self.__parse_memory (x)),
                'input-file': (lambda: self.input, self.__set_input, lambda x: self.__parse_file (x)),
                'output-file': (lambda: self.output, self.__set_output, lambda x: self.__parse_file (x)),
                'solution': (lambda: self.solution, self.__set_solution, lambda x: self.__find_solution (x))
                # TODO: configure checker, validator…
  #if 'checker' in problem_configuration:
  #  checker_name = problem_configuration['checker']
  #  if checker_name.startswith('testlib/'):
  #    # TODO: configure checker path somewhere
  #    checker_name = '/home/burunduk3/code/testlib-ro/trunk/checkers/' + checker_name[8:] + '.cpp'
  #  checker = find_source(checker_name)
            }
            for key, value in self.__parse_problem_properties (pp_file):
                try:
                    getter, setter, modifier = pp_morph[key]
                except KeyError:
                    self._t.log.warning ('[%s]: ignored option: %s' % (pp_file, key))
                    continue
                value = modifier (value)
                if value == getter ():
                    continue
                self._t.log ('[%s]: set %s to %s' % (pp_file, key, value))
                setter (value)
        # TODO: scan problem.xml
        detectors = [
            ('generator', lambda: self.generator, lambda: self.__autodetect_generator ()),
            ('validator', lambda: self.validator, lambda: self.__autodetect_validator ()),
            ('checker', lambda: self.checker, lambda: self.__autodetect_checker ())
        ]
        for name, key, setter in detectors:
            if key () is not None:
                continue
            if not setter ():
                continue
            self._t.log.notice ("[problem %s]: found %s: %s" % (self.name, name, key ()))

    def cleanup ( self ):
        if not os.path.isdir ('.tests'):
            os.mkdir ('.tests')
        for filename in os.listdir ('.tests'):
            if not re.match('^\d+(\.a)?$', filename):
                continue
            os.remove (os.path.join ('.tests', filename))
    def autogenerate ( self ):
        directory = 'source'
        if not os.path.isdir (directory):
            directory = 'tests'
        if not os.path.isdir (directory):
            raise Exception ('[problem %s]: failed to find source directory' % self.name)
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
                generator = heuristic.Source.find ('do' + test)
                if generator is None:
                    generator = heuristic.Source.find ('gen' + test) 
                if generator is None:
                    continue
                result = generator.run (stdout=open (target, 'w'))
                if not result:
                    log.error('generator (%s) failed' % generator)
                    failure = True
                else:
                    count_gen += 1
        if count_hand != 0:
            self._t.log ('manual tests copied: %d' % count_hand)
        if count_gen != 0:
            self._t.log ('generated tests: %d' % count_gen)
        return not failure
    def autofind_tests ( self, directory ):
        count = 0
        for filename in sorted (os.listdir (directory)):
            if not re.match ('^\d{2,3}$', filename):
                continue
            if not os.path.isfile (os.path.join (directory, filename)):
                continue
            target = os.path.join ('.tests', '%d' % count)
            shutil.move (os.path.join (directory, filename), target)
            count += 1
        return True
    def research_tests ( self ):
        self.__tests = []
        for x in map (lambda i: os.path.join ('.tests', '%d' % i), itertools.count ()):
            if not os.path.isfile (x):
                break
            self.__tests.append (x)

  #if 'source-directory' not in configuration:
  #    for directory in ['source', 'src', 'tests']:
  #      if os.path.isdir(os.path.join(path, directory)):
  #        configuration.update({'source-directory': os.path.join(path, directory)})
  #        break
  #if 'tests-directory' not in configuration:
  #    configuration.update({'tests-directory': os.path.join(path, 'tests')})
  #return configuration


    @classmethod
    def new ( self, datalog='.datalog', *, t ):
        return Problem (datalog, create=True, t=t)

    @classmethod
    def open ( self, path=os.path.abspath ('.'), datalog='.datalog', *, t):
        return Problem (os.path.join (path, datalog), t=t)

