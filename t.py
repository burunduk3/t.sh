#!/usr/bin/env python3
# -*- coding: utf8 -*-
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

import os
import re
import shutil
import sys
import json
import base64
import socket
import argparse

from tlib.common import Error, Log
from problem import Problem
import heuristic
import help
import legacy
from invoker import Invoker, RunResult

# === CHANGE LOG ===
#  2010-11-17 [burunduk3] work started



def testset_answers ( problem, *, tests=None, force=False, quiet=False ):
    global log
    if problem.solution is None:
        raise Error ('[problem %s]: solution not found' % problem.name)
    problem.solution.compile ()
    if not quiet:
        log ('generate answers', end='')
    input_name, output_name = '.temp/input', '.temp/output'
    if type (problem.input) is Problem.File.Name:
        input_name = os.path.join ('.temp', str (problem.input))
    if type (problem.output) is Problem.File.Name:
        output_name = os.path.join ('.temp', str (problem.output))
    if tests is None:
        tests = problem.tests
    for test in tests:
        if os.path.isfile (test + '.a') and not force:
            if not quiet:
                log ('+', prefix=False, end='')
            continue
        if not quiet:
            log ('.', prefix=False, end='')
        shutil.copy (test, input_name)
        r = problem.solution.run (
            directory='.temp',
            stdin=open (input_name, 'r') if type (problem.input) is Problem.File.Std else None,
            stdout=open (output_name, 'w') if type (problem.output) is Problem.File.Std else None
        )
        if not r:
            raise Error ('[problem %s]: solution failed on test %s.' % (problem.name, test))
        shutil.copy (output_name, test + '.a')
    if not quiet:
        log ('done', prefix=False)


def build_problem ( problem ):
    global log
    path = problem.path
    log ('== building problem “%s” ==' % problem.name)
    config_names = [
        ('path', problem.path),
        ('time limit', problem.limit_time),
        ('memory limit', problem.limit_memory),
        ('checker', problem.checker),
        ('solution', problem.solution),
        ('generator', problem.generator),
        ('validator', problem.validator),
        ('input', problem.input),
        ('output', problem.output),
        # ('default solution', ...),
        # ('source directory', ...)
    ]
    for name, value in config_names:
        if value is None:
            continue
        log ('  * %s: %s' % (name, value))
    os.chdir (path)
    if not os.path.isdir ('.temp'):
        os.mkdir ('.temp')
    if problem.solution is None:
        log.warning('No solution defined for problem %s.' % problem.name)
    problem.cleanup ()
    generator = problem.generator
    assert generator is not None
    result = generator.run ()
    if not result:
        raise Error ('[problem %s]: generator failed: %s' % (problem.name, generator))
    problem.research_tests ()
    if not problem.tests:
        raise Error ('[problem %s]: no tests found' % problem.name)
    log('tests (total: %d): [%s]' % (len (problem.tests), ' '.join (problem.tests)))
    # TODO: convert_tests(tests), move to generation, for copy
    validator = problem.validator
    if validator is not None:
        validator.compile ()
        log('validate tests', end='')
        for test in problem.tests:
            log ('.', prefix=False, end='')
            if validator.run (test, stdin=open(test, 'r')):
                continue
            raise Error('[problem %s]: validation failed: %s' % (problem.name, test))
        log ('done', prefix=False)
    testset_answers (problem)


class Test:
    FILE, GENERATOR = range (2)

    def __init__ ( self, problem=None, path=None, generator=None, name=None ):
        self.__problem = problem
        self.__path = path
        self.__name = name
        if self.__name is None:
            self.__name = self.__path
        if self.__name is None:
            self.__name = '<unknown>'
        if generator is not None:
            self.__type = Test.GENERATOR
            self.__generator = generator
        elif path is not None:
            self.__type = Test.FILE
        else:
            raise Exception ("failed to create test: unknown type")

    def __str__ ( self ):
        return self.__name

    def create ( self ):
        return {
            Test.FILE: lambda: self.__path,
            Test.GENERATOR: lambda: self.__create_generate ()
        } [self.__type] ()

    def __create_generate ( self ):
        assert self.__type is Test.GENERATOR
        path = '.temp/00' if self.__path is None else self.__path
        result = self.__generator.run (stdout=open(path, 'w'))
        # TODO: validate test
        testset_answers (self.__problem, tests=[path], force=True, quiet=True)
        if not result:
            raise Error ('generator (%s) failed' % self.__generator)
            return None
        return path

    @classmethod
    def file ( self, path, problem=None, name=None ):
        return Test (problem, path=path, name=name)

    @classmethod
    def generate ( self, generator, problem=None, name=None ):
        return Test (problem, generator=generator, name=name)


def tests_export ( problem ):
    os.chdir (problem.path)
    if not problem.tests:
        problem.research_tests ()
    tests = [Test.file (x) for x in problem.tests]
    if not tests:
        raise Error ('[problem %s]: no tests found' % problem.name)
    if not os.path.isdir ('tests'):
        os.mkdir ('tests')
    pattern = '%02d'
    if len (tests) >= 100:
        pattern = '%03d'
    if len (tests) >= 1000:
        raise Error ("[problem %s]: too many tests (%d)" % (problem.name, len (tests)))
    n = 0
    for i, x in enumerate (tests):
        test = x.create ()
        name = pattern % (i + 1)
        shutil.copy (test, os.path.join ('tests', name))
        shutil.copy (test + '.a', os.path.join ('tests', name) + '.a')
        n += 1
    log ('pattern: %s, tests copied: %d' % (pattern, n))


def check_problem ( problem, *, solution=None, tests=None, quiet=False, t ):
    global log
    os.chdir (problem.path)
    if tests is None:
        if not problem.tests:
            problem.research_tests ()
        tests = [Test.file (x) for x in problem.tests]
    if not tests:
        raise Error ('[problem %s]: no tests found' % problem.name)
    checker = problem.checker
    if checker is None:
        raise Error ('[problem %s]: no checker found' % problem.name)
    checker.compile ()
    if solution is None:
        solution = problem.solution
    if solution is None:
        raise Error ('[problem %s]: no solution found' % problem.name)
    solution.compile ()
    if not quiet:
        log.info('checking solution: %s' % solution)
    input_name, output_name = '.temp/input', '.temp/output'
    if type (problem.input) is Problem.File.Name:
        input_name = os.path.join ('.temp', str (problem.input))
    if type (problem.output) is Problem.File.Name:
        output_name = os.path.join ('.temp', str (problem.output))
    invoker = Invoker (
        solution.executable, limit_time=problem.limit_time,
        limit_idle=problem.limit_idle, limit_memory=problem.limit_memory,
        t=t
    )
    for i, x in enumerate (tests):
        test = x.create ()
        test_name = '#%02d' % (i + 1)
        log ('test %s [%s] ' % (test_name, x), end='')
        shutil.copy (test, input_name)
        r = invoker.run (
            directory='.temp',
            stdin=open (input_name, 'r') if type (problem.input) is Problem.File.Std else None,
            stdout=open (output_name, 'w') if type (problem.output) is Problem.File.Std else None
        )
        good = False
        if r.result == RunResult.RUNTIME:
            raise Error ('Runtime error (%s).' % r.comment)
        elif r.result == RunResult.TIME_LIMIT:
            raise Error ('Time limit exceeded (%s).' % r.comment)
        elif r.result == RunResult.MEMORY_LIMIT:
            raise Error ('Memory limit exceeded (%s)' % r.comment)
        elif r.result == RunResult.OK:
            good = True
        else:
            raise Error ('Invokation failed (%s).' % r.comment)
        if not good:
            return False
        log ('* ', prefix=False, end='')
        result = checker.run (input_name, output_name, test + '.a')
        if not result:
            log.error ('Wrong answer on test %s.' % test_name)
            return False
    return True


def find_source( path ):
    # used in Wolf
    return heuristic.source_find (path)


class WolfConnection:
    def __init__( self ):
        self.__socket = socket.socket()
        self.__socket.connect(('127.0.0.1', 1917))
        self.__tail = b''
        self.__queue = iter([])

    def query( self, j ):
        self.__socket.send((json.dumps(j) + '\n').encode('utf-8'))
        while True:
            r = next(self.__queue, None)
            if r is not None:
                return r
            data = self.__socket.recv(4096).split(b'\n')
            self.__tail += data[0]
            queue = []
            for x in data[1:]:
                queue.append(json.loads(self.__tail.decode('utf-8')))
                self.__tail = x
            self.__queue = iter(queue)


def wolf_export( problem, configuration, global_config ):
    log.info("== upload problem %s" % configuration['id'])
    os.chdir(configuration['tests-directory'])
    if 'full' not in configuration:
        raise Error ("cannot full name for problem %s" % configuration['id'])
    checker = None
    for checker_name in [
        'check', 'checker', 'check_' + configuration['id'], 'checker_' + configuration['id']
    ]:
        checker = find_source(os.path.join('..', checker_name))
        if checker is not None:
            break
    if checker is None:
        raise Error ('cannot find checker')
    wolf_compilers = {
        'delphi': 'win32.checker.delphi.ifmo',
        # 'delphi': 'win32.checker.delphi.kitten',
        'c++': 'win32.checker.c++',
        'perl': 'win32.perl'  # nothing special
    }
    checker_name = os.path.basename(checker)
    compiler = wolf_compilers[global_config.detect_language(checker).name]
    tests = [Test.file (x) for x in problem.tests]
    if not tests:
        raise T.Error('problem %s: no tests found' % problem)
    log('  name: %s' % configuration['id'])
    log('  full name: %s' % configuration['full'])
    log('  input file: %s' % configuration['input-file'])
    log('  output file: %s' % configuration['output-file'])
    log('  time limit: %s' % configuration['time-limit'])
    log('  memory limit: %s' % configuration['memory-limit'])
    log('  checker: %s (compiled with %s)' % (checker_name, compiler))
    log('tests (total: %d): %s' % (len(tests), ','.join(tests)))
    with open(checker, 'rb') as f:
        data = f.read()
        checker = base64.b64encode(data).decode('ascii')
    wolf = WolfConnection()
    assert wolf.query({'action': 'ping'}) is True
    log_write = lambda text: log (text, prefix=False, end='')
    log_write('send packets:')
    problem_id = wolf.query(
        {'action': 'problem.create', 'name': configuration['id'], 'full': configuration['full']}
    )
    assert isinstance(problem_id, int)
    log_write('.')
    assert wolf.query({
        'action': 'problem.files.set', 'id': problem_id, 'input': configuration['input-file'],
        'output': configuration['output-file']
    })
    log_write('.')
    assert wolf.query({
        'action': 'problem.limits.set', 'id': problem_id, 'time': configuration['time-limit'],
        'memory': configuration['memory-limit']
    })
    log_write('.')
    assert wolf.query({
        'action': 'problem.checker.set', 'id': problem_id, 'name': checker_name,
        'compiler': compiler, 'source': checker
    })
    log_write('.')
    for test in tests:
        with open(test, 'rb') as f:
            data = f.read()
            input = base64.b64encode(data).decode('ascii')
        with open(test + '.a', 'rb') as f:
            data = f.read()
            answer = base64.b64encode(data).decode('ascii')
        assert wolf.query(
            {'action': 'problem.test.add', 'id': problem_id, 'test': input, 'answer': answer}
        )
        log_write('.')
    log('', prefix='')
    log.info('uploaded, problem id: %d' % problem_id)


def clean_problem ( problem ):
    global log, options
    os.chdir (problem.path)
    remove_tests = 'no-remove-tests' not in options or not options['no-remove-tests']
    if remove_tests and os.path.isdir ('.tests'):
        for filename in os.listdir ('.tests'):
            ok = (filename in ("tests.description", "tests.gen"))
            ok = ok or re.match('^\d+(.a)?$', filename)
            if not ok:
                continue
            os.remove (os.path.join ('.tests', filename))
    for directory in ['.', '.tests', '.temp', 'tests', 'src', 'source', 'solutions']:
        if not os.path.isdir (directory):
            continue
        for filename in os.listdir (directory):
            ok = re.match (
                '^.*\.(in|out|log|exe|dcu|ppu|o|obj|class|hi|manifest|pyc|pyo)$', filename
            )
            ok = ok or re.match('^\d+(.a)?$', filename)
            ok = ok or filename in ("input", "output")
            if ok:
                os.remove (os.path.join (directory, filename))
            for suffix in heuristic.suffixes_all ():
                if not os.path.isfile (os.path.join (directory, filename + '.' + suffix)):
                    continue
                os.remove(os.path.join(directory, filename))
                break
        if remove_tests:
            cleaner = heuristic.source_find (os.path.join (directory, 'wipe'))
            if cleaner is None:
                continue
            if not cleaner.run ():
                log.warning ('%s returned non-zero' % cleaner)
    if (remove_tests and
        (os.path.isdir ('source') or os.path.isdir ('src')) and
        os.path.isdir ('tests')
    ):
        os.rmdir ('tests')
    for directory in ['.temp', '.tests']:
        if os.path.isdir (directory):
            os.rmdir (directory)


def prepare():
    import resource as r
    import signal as s
    global resource, signal
    resource, signal = r, s
    resource.setrlimit(resource.RLIMIT_STACK, (-1, -1))


# TODO: move into separate file
def prepare_windows():
    # Это выглядит как мерзкий, грязный хак, каковым является вообще любая работа с windows.
    import ctypes

    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE = -11
    STD_ERROR_HANDLE = -12

    FOREGROUND_BLUE = 0x01
    FOREGROUND_GREEN = 0x02
    FOREGROUND_RED = 0x04
    FOREGROUND_INTENSITY = 0x08
    BACKGROUND_BLUE = 0x10
    BACKGROUND_GREEN = 0x20
    BACKGROUND_RED = 0x40
    BACKGROUND_INTENSITY = 0x80
    windows_colors = [
        0,  # black
        FOREGROUND_RED,  # red
        FOREGROUND_GREEN,  # green
        FOREGROUND_GREEN | FOREGROUND_RED,  # brown
        FOREGROUND_BLUE,  # blue
        FOREGROUND_BLUE | FOREGROUND_RED,  # magenta
        FOREGROUND_BLUE | FOREGROUND_GREEN,  # skyblue
        FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_RED,  # gray
        0, 0, 0
    ]

    def windows_write( text, end='' ):
        text += end
        handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        pieces = text.split('\x1b[')
        sys.stdout.write(pieces[0])
        sys.stdout.flush()
        for str in pieces[1:]:
            color, line = str.split('m', 1)
            numbers = [int(x) for x in color.split(';')]
            mask = 0
            for x in numbers:
                if x == 0:
                    mask |= windows_colors[7]
                if x == 1:
                    mask |= FOREGROUND_INTENSITY
                if 30 <= x <= 39:
                    mask |= windows_colors[x - 30]
            ctypes.windll.kernel32.SetConsoleTextAttribute(handle, mask)
            sys.stdout.write(line.encode('utf8').decode('ibm866'))
            sys.stdout.flush()

    def windows_convert_tests( tests ):
        pass

    log.write = windows_write
    convert_tests = windows_convert_tests


class T:
    def __init__ ( self, log, configuration, legacy ):
        self.__log = log
        self.__configuration = configuration
        self.__problems = None
        self.__legacy = legacy
        self.__languages = {}

    log = property (lambda self: self.__log)
    languages = property (lambda self: self.__languages)

    def set_languages ( self, languages ):
        self.__languages = languages

    def __foreach ( self, action ):
        if self.__problems is None:
            self.__explore ()
        for problem in self.__problems:
            action (problem)

    def __build ( self, problem, arguments ):
        build_problem (problem)
        if not check_problem (problem, t=self):
            raise Error ("problem check failed")

    def __check ( self, problem, arguments ):
        solution = None
        if len(arguments) >= 1:
            solution = heuristic.source_find (arguments[0], prefix=problem.name_short)
            if solution is None:
                raise Error ("solution not found: '%s'" % arguments[0])
        check_problem (problem, solution=solution, t=self)

    def __clean ( self, problem, arguments ):
        clean_problem (problem)

    def __stress ( self, problem, arguments ):
        try:
            generator, solution = arguments[:2]
        except ValueError as error:
            raise Error ("usage: t.py stress <generator> <solution>") from error
        generator, solution = [heuristic.source_find (x) for x in (generator, solution)]
        r = True
        while r:
            r = check_problem (problem, solution=solution, tests=[
                Test.generate (generator, problem=problem, name='<stress>')
            ], quiet=True, t=self )

    def __tests ( self, problem, *arguments ):
        tests_export (problem)

    def __wolf_export ( self, problem, *arguments ):
        problem_configuration = self.__legacy.read_configuration (problem)
        wolf_export (problem, problem_configuration, self.__legacy)

    def __problem_create ( self, uuid=None ):
        problem = Problem.new ()
        uuid = problem.create (uuid)
        self.__problems = [problem]
        self.__log ('create problem #%s' % uuid)

    def __problem_reset ( self, problem ):
        problem.reset ()
        heuristic.problem_rescan (problem, t=self)

    def __problem_rescan ( self, problem ):
        heuristic.problem_rescan (problem, t=self)

    def __problem_set ( self, problem, arguments ):
        raise Error ("TODO")

    def __help ( self, par='disclaimer' ):
        sys.stdout.write ({
            'disclaimer': help.disclaimer,
            'gpl:c': help.license,
            'gpl:w': help.warranty,
        }[par])

    def __call__ ( self, arguments ):
        command = arguments[0]
        actions = {
            x: (
                lambda command, args, y=y: self.__foreach (lambda problem: y (problem, args))
            ) for x, y in [
                ('build', self.__build),
                ('check', self.__check),
                ('clean', self.__clean),
                ('stress', self.__stress),
                ('tests', self.__tests),
                ('problem:reset', self.__problem_reset),
                ('problem:rescan', self.__problem_rescan),
                ('problem:set', self.__problem_set),
                ('wolf:export', self.__wolf_export)
            ]
        }
        actions.update ({
            'problem:create': lambda command, args: self.__problem_create (*args),
            'help': lambda command, args: self.__help (*args)
        })
        try:
            action = actions[command]
        except KeyError as error:
            raise Error ("unknown command: '%s'" % command) from error
        action (command, arguments[1:])

    def __explore ( self, recursive=None ):
        if recursive is None:
            recursive = self.__configuration['recursive']
        if recursive:
            self.__problems = list (heuristic.find_problems (t=self))
        else:
            self.__problems = [heuristic.problem_open (t=self)]
        for problem in self.__problems:
            if problem.uuid is None:
                problem.create ()


def arguments_parse():
    parser = argparse.ArgumentParser (description='t.py: programming contest problem helper')
    parser.add_argument (
        '--no-remove-tests', '-t', dest='remove_tests', action='store_false', default=True
    )
    parser.add_argument ('--recursive', '-r', dest='recursive', action='store_true', default=False)
    parser.add_argument ('--verbose', '-v', dest='verbose', action='store_true', default=False)
    parser.add_argument ('command', nargs='+')
    args = parser.parse_args ()
    options = {
        'no-remove-tests': not args.remove_tests,
        'recursive': args.recursive,
        'verbose': args.verbose
    }
    return options, args.command


if sys.platform == 'win32':  # if os is outdated
    prepare = prepare_windows

options, arguments = arguments_parse()

log = Log()
prepare()

configuration = legacy.Configuration()
tpy = T (log, options, configuration)
languages = heuristic.compilers_configure ( configuration, tpy )
tpy.set_languages (languages)

try:
    if options['verbose']:
        log.verbose ()
    tpy (arguments)
except Error as e:
    log.error (e)
    sys.exit (1)
except KeyboardInterrupt:
    log.info ("^C")
    sys.exit (2)

