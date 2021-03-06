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

import itertools
import time

from . import common


class Type:
    def __init__ ( self, t ):
        self._t = t

    def __str__ ( self ):
        raise common.Error ()

    def dump ( self ):
        raise common.Error ()

    def __eq__ ( self, x ):
        raise common.Error ()

    @classmethod
    def dumps ( cls, value ):
        yield from cls (value).dump ()
    
    _log = property (lambda self: self._t.log)


class Datalog (common.Module):
    class NotFound (Exception):
        pass

    # use write=True to save data in memory, readonly=True for deny any change
    def __init__ ( self, datalog, actions={}, *, create=False, write=True, readonly=False, t ):
        super (Datalog, self).__init__ (t)
        common.Error.ensure (write or not create, "incorrect arguments")
        self._actions = actions
        self._time = 0
        self.__readonly = readonly
        if self.__readonly:
            write = False
        try:
            with open (datalog, 'r') as log:
                for line in log.readlines ():
                    self.__event (line.strip ())
        except FileNotFoundError as error:
            if create:
                self._t.log.warning ("file not found: '%s', create new" % datalog)
            elif write:
                raise Datalog.NotFound from error
        if write:
            self.__datalog = open (datalog, 'a')
        else:
            self.__datalog = None

    def _upgrade ( self, key, action ):
        common.Error.ensure (key not in self._actions, "datalog keys must be unique")
        self._actions[key] = action

    def __precheck ( self, line ):
        ts, event, *data = line.split (' ', 2)
        if self._time > int (ts):
            return None
        if event not in self._actions:
            return None
        return True

    @staticmethod
    def __parse ( line ):
        token = ''

        def state_default ( x ):
            nonlocal token
            if x == ' ' or x == '\n':
                if len (token):
                    yield token
                token = ''
            elif x != '"':
                token += x
            else:
                return state_str
            return state_default

        def state_str ( x ):
            nonlocal token
            if x == '"':
                yield token
                token = ''
                return state_default
            if x == '\\':
                return state_backslash
            token += x
            return state_str

        def state_backslash ( x ):
            nonlocal token
            conv = {'n': '\n', 'r': '\r', 't': '\t', '0': '\0'}
            token += conv.get (x, x)
            return state_str

        state = state_default
        for x in line:
            state = yield from state (x)
        yield from state ('\n')
        common.Error.ensure (state is state_default, "parse failed")


    def __event ( self, line ):
        ts, event, *data = line.split (' ', 2)
        if len (data):
            data = data[0]
        else:
            data = ''
        self._time = int (ts)
        return self._actions[event] ( self.__parse (data))

    @staticmethod
    def __logevent ( now, event, *args ):
       yield now
       yield event
       for x in args:
           for y in x.dump ():
               yield y

    def _commit ( self, event, *args, check=True ):
        common.Error.ensure (not self.__readonly, "datalog commit failed: readonly")
        now = str (int (time.time ()))
        line = ' '.join (self.__logevent (now, event, *args))
        if check:
            common.Error.ensure (self.__precheck (line), "datalog commit failed: precheck failed")
        if self.__datalog is not None:
            print (line, file=self.__datalog)
            self.__datalog.flush ()
        return self.__event (line.strip ())

        # try:
            #    os.path.join (path, datalog),
            #    create=(datalog_write and force is not None),
            #    write=datalog_write,
        # except Datalog.NotFound as error:
        # if problem.uuid is None:
        #     p.create ()
#     def __init__ ( self, datalog, **kwargs ):
#         self.__uuid = None
#         super (Problem, self).__init__ (datalog, actions={
#             Problem.LEV_CREATE: self.__lev_create
#         }, **kwargs)
# 
# class Problem (Datalog):
#     TYPE_GENERATOR = range (1)
# 
#     LEV_CREATE = 'problem.create'
#     LEV_RESET = 'problem.reset'
#     LEV_NAME_SHORT = 'problem.name_short'
#     LEV_LIMIT_TIME = 'problem.limit_time'
#     LEV_LIMIT_IDLE = 'problem.limit_idle'
#     LEV_LIMIT_MEMORY = 'problem.limit_memory'
#     LEV_INPUT = 'problem.input'
#     LEV_INPUT_STD = 'problem.input.std'
#     LEV_OUTPUT = 'problem.output'
#     LEV_OUTPUT_STD = 'problem.output.std'
#     LEV_CHECKER = 'problem.checker'
#     LEV_SOLUTION = 'problem.solution'
#     LEV_GENERATOR_EXT = 'problem.generator.external'
#     LEV_VALIDATOR = 'problem.validator'
# 
#     class File (Type):
#         class Std (Type):
#             def __init__ ( self, *, t ):
#                 super (Problem.File.Std, self).__init__ (t=t)
# 
#             def __str__ ( self ):
#                 return '<std>'
# 
#             def __eq__ ( self, x ):
#                 return type (self) is type (x)
# 
#         class Name (Type):
#             def __init__ ( self, name, *, t ):
#                 super (Problem.File.Name, self).__init__ (t=t)
#                 self.__name = name
# 
#             def __str__ ( self ):
#                 return self.__name
# 
#             def __eq__ ( self, x ):
#                 if type (self) is not type (x):
#                     return False
#                 return self.__name == x.__name
# 
#         @classmethod
#         def std ( cls, t ):
#             return Problem.File.Std (t=t)
# 
#         @classmethod
#         def name ( cls, name, t ):
#             return Problem.File.Name (name, t=t)
# 
# 
#     class Generator (Type):
#         def __init__ ( self, problem, source, directory, *, t ):
#             super (Problem.Generator, self).__init__ (t=t)
#             self.__problem = problem
#             self.__source = source
#             self.__directory = directory
# 
#         def commit ( self ):
#             return (Problem.LEV_GENERATOR_EXT, self.__source, types.String (self.__directory))
# 
#         def __str__ ( self ):
#             return str (self.__source)
# 
#         def __eq__ ( self, x ):
#             if type (self) is not type (x):
#                 return False
#             return self.__source == x.__source
# 
#         def run ( self ):
#             r = self.__source.run (directory=self.__directory)
#             if not r:
#                 raise Error ('generator failed: %s' % self)
#             return self.__problem.autofind_tests ('tests')
# 
#     # handle logevents
# 
#     def __lev_create ( self, data ):
#         self.__uuid = next (data)
#         self._actions = {
#             Problem.LEV_RESET: self.__lev_reset,
#             Problem.LEV_NAME_SHORT: self.__lev_name_short,
#             Problem.LEV_LIMIT_TIME: self.__lev_limit_time,
#             Problem.LEV_LIMIT_IDLE: self.__lev_limit_idle,
#             Problem.LEV_LIMIT_MEMORY: self.__lev_limit_memory,
#             Problem.LEV_INPUT: self.__lev_input_name,
#             Problem.LEV_INPUT_STD: self.__lev_input_std,
#             Problem.LEV_OUTPUT: self.__lev_output_name,
#             Problem.LEV_OUTPUT_STD: self.__lev_output_std,
#             Problem.LEV_CHECKER: self.__lev_checker,
#             Problem.LEV_SOLUTION: self.__lev_solution,
#             # Problem.LEV_GENERATOR_AUTO: self.__lev_generator_auto,
#             Problem.LEV_GENERATOR_EXT: self.__lev_generator_external,
#             Problem.LEV_VALIDATOR: self.__lev_validator
#         }
#         for type, key, action in self._t.problem_upgrades:
#             def assign_generator ( value ):
#                 nonlocal self
#                 self.__generator = value
# 
#             self._upgrade (key, lambda data, self=self: {
#                 Problem.TYPE_GENERATOR: assign_generator
#             } [type] (action (self, data)))
#         return self.__uuid
# 
#     def __lev_reset ( self, data ):
#         self.__name_short = None
#         self.__limit_time = None
#         self.__limit_idle = None
#         self.__limit_memory = None
#         self.__input = None
#         self.__output = None
#         self.__solution = None
#         self.__generator = None
#         self.__validator = None
#         self.__checker = None
# 
#     def __lev_name_short ( self, data ):
#         self.__name_short = types.String.parse (data)
#         return True
# 
#     def __lev_limit_time ( self, data ):
#         self.__limit_time = types.Float.parse (data)
#         return True
# 
#     def __lev_limit_idle ( self, data ):
#         self.__limit_idle = types.Float.parse (data)
#         return True
# 
#     def __lev_limit_memory ( self, data ):
#         self.__limit_memory = types.Integer.parse (data)
#         return True
# 
#     def __lev_input_std ( self, data ):
#         self.__input = Problem.File.std (t=self._t)
#         return True
# 
#     def __lev_input_name ( self, data ):
#         self.__input = Problem.File.name (next (data), t=self._t)
#         return True
# 
#     def __lev_output_std ( self, data ):
#         self.__output = Problem.File.std (t=self._t)
#         return True
# 
#     def __lev_output_name ( self, data ):
#         self.__output = Problem.File.name (next (data), t=self._t)
#         return True
# 
#     def __lev_checker ( self, data ):
#         self.__checker = types.Source.parse (data, self._languages)
#         return True
# 
#     def __lev_solution ( self, data ):
#         self.__solution = types.Source.parse (data, self._languages)
#         return True
# 
#     def __lev_generator_external ( self, data ):
#         generator = types.Source.parse (data, self._languages)
#         directory = next (data)
#         self.__generator = Problem.Generator (self, generator, directory, t=self._t)
#         return True
# 
#     def __lev_validator ( self, data ):
#         self.__validator = types.Source.parse (data, self._languages)
#         return True
# 
#     def canonical ( self, routine ):
#         fields = [
#             ('name', lambda: self.name_short, self.__set_name_short, None),
#             ('input', lambda: self.input, self.__set_input, lambda: self.__set_input_std ()),
#             ('output', lambda: self.output, self.__set_output, lambda: self.__set_output_std ()),
#             ('time limit', lambda: self.limit_time, self.__set_limit_time, None),
#             ('idle limit', lambda: self.limit_idle, self.__set_limit_idle, None),
#             ('memory limit', lambda: self.limit_memory, self.__set_limit_memory, None),
#             ('solution', lambda: self.solution, self.__set_solution, None),
#         ]
#         for args in fields:
#             routine (*args)
# 
#     def create ( self, uuid=None ):
#         if uuid is None:
#             uuid = ''.join (['%x' % random.randint (0, 15) for x in range (32)])
#         return self._commit (Problem.LEV_CREATE, types.String (uuid))
# 
#     def reset ( self ):
#         return self._commit (Problem.LEV_RESET)
# 
#     path = property (lambda self: self.__path)
#     uuid = property (lambda self: self.__uuid)
# 
#     def __set_name_short ( self, value ):
#         return self._commit (Problem.LEV_NAME_SHORT, types.String (value))
#     name_short = property (
#         lambda self: self.__name_short.value if self.__name_short is not None else None,
#         __set_name_short
#     )
# 
#     def __set_limit_time ( self, value ):
#         return self._commit (Problem.LEV_LIMIT_TIME, types.Float (value))
#     limit_time = property (
#         lambda self: self.__limit_time.value if self.__limit_time is not None else None,
#         __set_limit_time
#     )
# 
#     def __set_limit_idle ( self, value ):
#         return self._commit (Problem.LEV_LIMIT_IDLE, types.Float (value))
#     limit_idle = property (
#         lambda self: self.__limit_idle.value if self.__limit_idle is not None else None,
#         __set_limit_idle
#     )
# 
#     def __set_limit_memory ( self, value ):
#         return self._commit (Problem.LEV_LIMIT_MEMORY, types.Integer (value))
#     limit_memory = property (
#         lambda self: self.__limit_memory.value if self.__limit_memory is not None else None,
#         __set_limit_memory
#     )
# 
#     def __set_input_std ( self ):
#         return self._commit (Problem.LEV_INPUT_STD)
# 
#     def __set_input_name ( self, value ):
#         return self._commit (Problem.LEV_INPUT, types.String (value))
# 
#     def __set_input ( self, value ):
#         if type (value) is Problem.File.Std:
#             return self.__set_input_std ()
#         if type (value) is Problem.File.Name:
#             return self.__set_input_name (str (value))
#         raise Error ("bad input value: %s" % str (value))
#     input = property (lambda self: self.__input, __set_input)
# 
#     def __set_output_std ( self ):
#         return self._commit (Problem.LEV_OUTPUT_STD)
# 
#     def __set_output_name ( self, value ):
#         return self._commit (Problem.LEV_OUTPUT, types.String (value))
# 
#     def __set_output ( self, value ):
#         if type (value) is Problem.File.Std:
#             return self.__set_output_std ()
#         if type (value) is Problem.File.Name:
#             return self.__set_output_name (str (value))
#         raise Error ("bad output value: %s" % str (value))
#     output = property (lambda self: self.__output, __set_output)
# 
#     def __set_checker ( self, value ):
#         return self._commit (Problem.LEV_CHECKER, value)
#     checker = property (lambda self: self.__checker, __set_checker)
# 
#     def __set_solution ( self, value ):
#         return self._commit (Problem.LEV_SOLUTION, value)
#     solution = property (lambda self: self.__solution, __set_solution)
# 
#     def __set_generator ( self, value ):
#         lev, *args = value.commit ()
#         return self._commit (lev, *args)
#     generator = property (lambda self: self.__generator, __set_generator)
# 
#     def __set_validator ( self, value ):
#         return self._commit (Problem.LEV_VALIDATOR, value)
#     validator = property (lambda self: self.__validator, __set_validator)
# 
#     name = property (
#         lambda self: self.__name_short if self.__name_short is not None else self.__uuid
#     )
#     tests = property (lambda self: self.__tests)
# 
#     def cleanup ( self ):
#         if not os.path.isdir ('.tests'):
#             os.mkdir ('.tests')
#         for filename in os.listdir ('.tests'):
#             if not re.match('^\d+(\.a)?$', filename):
#                 continue
#             os.remove (os.path.join ('.tests', filename))
# 
#     @classmethod
#     def new ( self, datalog='.datalog', *, t ):
#         return Problem (datalog, create=True, t=t)

