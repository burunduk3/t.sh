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

import itertools
import os
import os.path
import random
import re
import shutil
import struct

from tlib.common import Error
from tlib.datalog import Datalog, Type
from tlib import types
import heuristic


class Problem (Datalog):
    @classmethod
    def parse_memory ( self, value ):
        for suffix, multiplier in [('K', 2**10), ('M', 2**20), ('G', 2**30), ('T', 2**40), ('', 1)]:
            if value.endswith(suffix):
                return int (value[0:-len (suffix)]) * multiplier
        assert False

    @classmethod
    def parse_file ( self, value, *, t ):
        if value in ('<std>', '<stdin>', '<stdout>'):
            return Problem.File.std (t=t)
        return Problem.File.name (value, t=t)

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
            def __init__ ( self, *, t ):
                super (Problem.File.Std, self).__init__ (t=t)

            def __str__ ( self ):
                return '<std>'

            def __eq__ ( self, x ):
                return type (self) is type (x)

        class Name (Type):
            def __init__ ( self, name, *, t ):
                super (Problem.File.Name, self).__init__ (t=t)
                self.__name = name

            def __str__ ( self ):
                return self.__name

            def __eq__ ( self, x ):
                if type (self) is not type (x):
                    return False
                return self.__name == x.__name

        @classmethod
        def std ( cls, t ):
            return Problem.File.Std (t=t)

        @classmethod
        def name ( cls, name, t ):
            return Problem.File.Name (name, t=t)


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

    class Generator (Type):
        class Auto (Type):
            def __init__ ( self, problem, *, t):
                super (Problem.Generator.Auto, self).__init__ (t=t)
                self.__problem = problem

            def __str__ ( self ):
                return '<automatic>'

            def __eq__ ( self, x ):
                return type (self) is type (x)

            def run ( self ):
                return self.__problem.autogenerate ()

        class External (Type):
            def __init__ ( self, problem, source, directory, *, t ):
                super (Problem.Generator.External, self).__init__ (t=t)
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
                    raise Error ('generator failed: %s' % self)
                return self.__problem.autofind_tests ('tests')

        @classmethod
        def auto ( cls, problem, *, t ):
            return Problem.Generator.Auto (problem, t=t)

        @classmethod
        def external ( cls, problem, source, directory, *, t ):
            return Problem.Generator.External (problem, source, directory, t=t)

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
            Problem.LEV_CREATE: self.__lev_create
        }, create=create, t=t)
        self.__tests = None

    # handle logevents

    def __lev_create ( self, data ):
        self.__uuid = next (data)
        self._actions = {
            Problem.LEV_NAME_SHORT: self.__lev_name_short,
            Problem.LEV_LIMIT_TIME: self.__lev_limit_time,
            Problem.LEV_LIMIT_IDLE: self.__lev_limit_idle,
            Problem.LEV_LIMIT_MEMORY: self.__lev_limit_memory,
            Problem.LEV_INPUT: self.__lev_input_name,
            Problem.LEV_INPUT_STD: self.__lev_input_std,
            Problem.LEV_OUTPUT: self.__lev_output_name,
            Problem.LEV_OUTPUT_STD: self.__lev_output_std,
            Problem.LEV_CHECKER: self.__lev_checker,
            Problem.LEV_SOLUTION: self.__lev_solution,
            Problem.LEV_GENERATOR_AUTO: self.__lev_generator_auto,
            Problem.LEV_GENERATOR_EXT: self.__lev_generator_external,
            Problem.LEV_VALIDATOR: self.__lev_validator
        }
        return self.__uuid

    def __lev_name_short ( self, data ):
        self.__name_short = types.String.parse (data)
        return True

    def __lev_limit_time ( self, data ):
        self.__limit_time = types.Float.parse (data)
        return True

    def __lev_limit_idle ( self, data ):
        self.__limit_idle = types.Float.parse (data)
        return True

    def __lev_limit_memory ( self, data ):
        self.__limit_memory = types.Integer.parse (data)
        return True

    def __lev_input_std ( self, data ):
        self.__input = Problem.File.std (t=self._t)
        return True

    def __lev_input_name ( self, data ):
        self.__input = Problem.File.name (next (data), t=self._t)
        return True

    def __lev_output_std ( self, data ):
        self.__output = Problem.File.std (t=self._t)
        return True

    def __lev_output_name ( self, data ):
        self.__output = Problem.File.name (next (data), t=self._t)
        return True

    def __lev_checker ( self, data ):
        self.__checker = types.Source.parse (data, self._languages)
        return True

    def __lev_solution ( self, data ):
        self.__solution = types.Source.parse (data, self._languages)
        return True

    def __lev_generator_auto ( self, data ):
        self.__generator = Problem.Generator.auto (self, t=self._t)
        return True

    def __lev_generator_external ( self, data ):
        generator = types.Source.parse (data, self._languages)
        directory = next (data)
        self.__generator = Problem.Generator.external (self, generator, directory, t=self._t)
        return True

    def __lev_validator ( self, data ):
        self.__validator = types.Source.parse (data, self._languages)
        return True

    def canonical ( self, routine ):
        fields = [
            ('name', lambda: self.name_short, self.__set_name_short, None),
            ('input', lambda: self.input, self.__set_input, lambda: self.__set_input_std ()),
            ('output', lambda: self.output, self.__set_output, lambda: self.__set_output_std ()),
            ('time limit', lambda: self.limit_time, self.__set_limit_time, None),
            ('idle limit', lambda: self.limit_idle, self.__set_limit_idle, None),
            ('memory limit', lambda: self.limit_memory, self.__set_limit_memory, None),
            ('solution', lambda: self.solution, self.__set_solution, None),
        ]
        for args in fields:
            routine (*args)

    def create ( self, uuid=None ):
        if uuid is None:
            uuid = ''.join (['%x' % random.randint (0, 15) for x in range (32)])
        return self._commit (Problem.LEV_CREATE, types.String (uuid))

    path = property (lambda self: self.__path)
    uuid = property (lambda self: self.__uuid)

    def __set_name_short ( self, value ):
        return self._commit (Problem.LEV_NAME_SHORT, types.String (value))
    name_short = property (
        lambda self: self.__name_short.value if self.__name_short is not None else None,
        __set_name_short
    )

    def __set_limit_time ( self, value ):
        return self._commit (Problem.LEV_LIMIT_TIME, types.Float (value))
    limit_time = property (
        lambda self: self.__limit_time.value if self.__limit_time is not None else None,
        __set_limit_time
    )

    def __set_limit_idle ( self, value ):
        return self._commit (Problem.LEV_LIMIT_IDLE, types.Float (value))
    limit_idle = property (
        lambda self: self.__limit_idle.value if self.__limit_idle is not None else None,
        __set_limit_idle
    )

    def __set_limit_memory ( self, value ):
        return self._commit (Problem.LEV_LIMIT_MEMORY, types.Integer (value))
    limit_memory = property (
        lambda self: self.__limit_memory.value if self.__limit_memory is not None else None,
        __set_limit_memory
    )

    def __set_input_std ( self ):
        return self._commit (Problem.LEV_INPUT_STD)

    def __set_input_name ( self, value ):
        return self._commit (Problem.LEV_INPUT, types.String (value))

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
        return self._commit (Problem.LEV_OUTPUT, types.String (value))

    def __set_output ( self, value ):
        if type (value) is Problem.File.Std:
            return self.__set_output_std ()
        if type (value) is Problem.File.Name:
            return self.__set_output_name (str (value))
        assert False
    output = property (lambda self: self.__output, __set_output)

    def __set_checker ( self, value ):
        return self._commit (Problem.LEV_CHECKER, value)
    checker = property (lambda self: self.__checker, __set_checker)

    def __set_solution ( self, value ):
        return self._commit (Problem.LEV_SOLUTION, value)
    solution = property (lambda self: self.__solution, __set_solution)

    def __set_generator_auto ( self ):
        return self._commit (Problem.LEV_GENERATOR_AUTO)

    def __set_generator_external ( self, value, directory ):
        return self._commit (Problem.LEV_GENERATOR_EXT, value, types.String (directory))
    generator = property (lambda self: self.__generator)

    def __set_validator ( self, value ):
        return self._commit (Problem.LEV_VALIDATOR, value)
    validator = property (lambda self: self.__validator, __set_validator)

    name = property (
        lambda self: self.__name_short if self.__name_short is not None else self.__uuid
    )
    tests = property (lambda self: self.__tests)

    def detect_generator ( self, detector ):
        return detector (self.__set_generator_auto, self.__set_generator_external)

    def cleanup ( self ):
        if not os.path.isdir ('.tests'):
            os.mkdir ('.tests')
        for filename in os.listdir ('.tests'):
            if not re.match('^\d+(\.a)?$', filename):
                continue
            os.remove (os.path.join ('.tests', filename))

    # TODO: move autogenerator into heurisctic
    def autogenerate ( self ):
        directory = 'source'
        if not os.path.isdir (directory):
            directory = 'src'
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
                generator = heuristic.source_find ('do' + test)
                if generator is None:
                    generator = heuristic.source_find ('gen' + test)
                if generator is None:
                    continue
                result = generator.run (stdout=open (target, 'w'))
                if not result:
                    raise self._t.Error ('generator (%s) failed' % generator)
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

        # if 'source-directory' not in configuration:
        #    for directory in ['source', 'src', 'tests']:
        #      if os.path.isdir(os.path.join(path, directory)):
        #        configuration.update({'source-directory': os.path.join(path, directory)})
        #        break
        # if 'tests-directory' not in configuration:
        #    configuration.update({'tests-directory': os.path.join(path, 'tests')})
        # return configuration

    @classmethod
    def new ( self, datalog='.datalog', *, t ):
        return Problem (datalog, create=True, t=t)

