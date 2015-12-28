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
import subprocess
import sys
import threading
import time
import json
import base64
import socket
import argparse
import traceback

import common as t
from problem import Problem
import heuristic
import help
import legacy

# === CHANGE LOG ===
#  2010-11-17 [burunduk3] work started


# === COMPILERS CONFIGURATION ==
# Здесь начинается конфигурация компиляторов. Мерзкая штука, не правда ли?

def compilers_configure():
    global configuration, suffixes

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

    configuration.compilers = {
        'bash': Compiler ('bash', executable=script ('bash')),
        'perl': Compiler ('perl', executable=script ('perl')),
        'python2': Compiler ('python2', executable=script ('python2')),
        'python3': Compiler ('python3', executable=script ('python3')),
        'c': Compiler ('c',
            binary=binary_default,
            command=lambda source, binary: ['gcc'] + flags_c + ['-x', 'c', '-o', binary, source],
            executable=executable_default
        ),
        'c++': Compiler ('c++',
            binary=binary_default,
            command=lambda source, binary: ['g++'] + flags_cpp + ['-x', 'c++', '-o', binary, source],
            executable=executable_default
        ),
        'delphi': Compiler ('delphi',
            binary=binary_default,
            command=lambda source, binary: ['fpc', '-Mdelphi', '-O3', '-FE.', '-v0ewn', '-Sd', '-Fu' + include_path, '-Fi' + include_path, '-d__T_SH__', '-o'+binary, source],
            # command=lambda source, binary: ['fpc', '-Mdelphi', '-O3', '-FE.', '-v0ewn', '-Sd', '-d__T_SH__', '-o'+binary, source],
            executable=executable_default
        ),
        'java': Compiler ('java',
            binary=lambda source: os.path.splitext(source)[0] + '.class',
            command=lambda source, binary: ['javac', '-cp', os.path.dirname(source), source],
            executable=lambda binary: Executable (binary, [
                'java', '-Xms8M', '-Xmx128M', '-Xss64M', '-ea',
                '-cp', os.path.dirname (binary) + java_cp_suffix,
                os.path.splitext (os.path.basename (binary))[0]
            ], add=False)
        ),
        'java.checker': Compiler ('java',
            binary=lambda source: os.path.splitext(source)[0] + '.class',
            command=lambda source, binary: ['javac', '-cp', os.path.dirname (source), source],
            executable=lambda binary: Executable (binary, [
                'java', '-Xms8M', '-Xmx128M', '-Xss64M', '-ea',
                "-cp", os.path.dirname(binary) + java_cp_suffix,
                "ru.ifmo.testlib.CheckerFramework", os.path.splitext (os.path.basename (binary))[0]
            ], add=False)
        ),
        'pascal': Compiler ('pascal',
            binary=binary_default,
            command=lambda source, binary: [
                'fpc', '-O3', '-FE.', '-v0ewn', '-Fu' + include_path, '-Fi' + include_path,
                '-d__T_SH__', '-o'+binary, source
            ],
            executable=executable_default
        ),
    }
    heuristic.set_compilers (configuration.compilers)

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
    suffixes = configuration.detector.keys()



# === PARTS OF t.sh ===

# # GCC flags
# gccVersionString=`gcc --version | head -n 1`
# gccVersion=${gccVersionString##* }
# gccVersionMajor=${gccVersion##*.}
# if [ $gccVersionMajor == "4" ] ; then
#   CFLAGS="-O2 -Wall -Wextra -I $INCLUDE_PATH -D__T_SH__"
# else
#   CFLAGS="-O2 -Wall -I $INCLUDE_PATH -D__T_SH__"
# fi
# CXXFLAGS="${CFLAGS}"
# # End of GCC flags
# BINARY_SUFFIX=""
# if [ "$OPERATION_SYSTEM" != "Linux" ]; then
#   CFLAGS="$CFLAGS -Wl,--stack=134217728"
#   CXXFLAGS="$CXXFLAGS -Wl,--stack=134217728"
#   BINARY_SUFFIX=".exe"
# fi

class Log:
  DEBUG, INFO, NOTICE, WARNING, ERROR, FATAL = range(6)
  def __init__( self ):
    self.__verbose = False
    self.color = {Log.DEBUG: 37, Log.INFO: 36, Log.NOTICE: 32, Log.WARNING: 33, Log.ERROR: 31, Log.FATAL: 31}
    self.message = {Log.DEBUG: 'debug', Log.INFO: 'info', Log.NOTICE: 'notice', Log.WARNING: 'warning', Log.ERROR: 'error', Log.FATAL: 'fatal error'}
    self.debug = lambda text: self(text, Log.DEBUG)
    self.info = lambda text: self(text, Log.INFO)
    self.notice = lambda text: self(text, Log.NOTICE)
    self.warning = lambda text: self(text, Log.WARNING)
    self.error = lambda text: self(text, Log.ERROR)
    self.fatal = lambda text: self(text, Log.FATAL)
    pass
  def __call__( self, message, level=INFO, *, exit=None, end='\n', verbose=False ):
    if verbose and not self.__verbose:
        return
    if verbose:
        self.write ("\x1b[1;%dm[t:%s,verbose]\x1b[0m %s" % (self.color[level], self.message[level], message), end=end)
    else:
        self.write ("[t:%s] \x1b[1;%dm%s\x1b[0m" % (self.message[level], self.color[level], message), end=end)
    exit = exit if exit is not None else level >= Log.ERROR
    if exit:
        # TODO: remove this
        sys.exit(1)
  def verbose ( self ):
      self.__verbose = True
  def write( self, message, end='', color=None ):
    if color is not None:
      message = "\x1b[1;%dm%s\x1b[0m" % (self.color[color], message)
    print(message, end=end)
    sys.stdout.flush()


class Configuration:
  # TODO: remove this somehow
  def __init__( self ):
    self.compilers = {}
    self.detector = {}
  def detect_language( self, source ):
    if source.endswith('Check.java'):
        return self.compilers["java.checker"]
    suffix = os.path.splitext(source)[1][1:]
    if suffix not in self.detector:
      return None
    detector = self.detector[suffix]
    if type(detector) == str:
      return self.compilers[detector]
    return self.compilers[detector(source)]


compile_cache = {}

class Compiler:
  def __init__( self, name, *, binary=None, command=None, executable=None ):
    self.binary, self.command, self.executable = binary, command, executable
    if binary is None:
        self.binary = lambda source: source
    self.name = name
  def __call__( self, source ):
    global log, compile_cache
    if not source.startswith ('/'):
        source = os.path.join (os.getcwd (), source)
    if source in compile_cache:
        return compile_cache[source]
    binary = self.binary(source)
    if binary == source or self.command is None or (os.path.isfile(binary) and os.stat(binary).st_mtime >= os.stat(source).st_mtime):
      log ('compile skipped: %s' % binary)
    else:
      log ('compile: %s → %s' % (source, binary))
      command = self.command(source, binary)
      log ('$ %s' % (' '.join (command)), verbose=True)
      process = subprocess.Popen(command)
      process.communicate()
      if process.returncode != 0:
        return None
    compile_cache[source] = self.executable(binary)
    return compile_cache[source]


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
  def __call__( self, arguments=[], directory=None, stdin=None, stdout=None, stderr=None ):
    process = subprocess.Popen (
        self.command + list (arguments), cwd=directory, stdin=stdin, stdout=stdout, stderr=stderr
    )
    process.communicate ()
    return process.returncode == 0

class RunResult:
  RUNTIME, TIME_LIMIT, MEMORY_LIMIT, OK = range(4)
  def __init__( self, result, exitcode, comment='' ):
    self.result, self.exitcode, self.comment = result, exitcode, comment

class Invoker:
    def __init__( self, executable, *, limit_time, limit_idle, limit_memory ):
        self.__executable = executable
        self.__limit_time = limit_time
        self.__limit_idle = limit_idle
        self.__limit_memory = limit_memory
        self.__process = None
        self.__condition = None

    def __waiter( self ):
        self.__process.communicate()
        self.__condition.acquire()
        self.__condition.notify()
        self.__condition.release()

    def run( self, *, directory=None, stdin=None, stdout=None, stderr=None ):
        global log
    # limit resources of current process: bad idea
    # resource.setrlimit(resource.RLIMIT_CPU, ((int)(self.limit_time + 2), -1))
    # resource.setrlimit(resource.RLIMIT_DATA, (self.limit_memory, -1))
        start = time.time ()
        self.__process = subprocess.Popen (
            self.__executable.command, cwd=directory, stdin=stdin, stdout=stdout, stderr=stderr
        )
        pid = self.__process.pid
        self.__condition = threading.Condition()
        thread = threading.Thread(target=self.__waiter)
        # wait, what?
        thread.start()
        force_result = None
        while True:
            self.__condition.acquire()
            self.__condition.wait(0.01)
            self.__condition.release()
            if self.__process.returncode is not None:
                break
            try: # так может случится, что процесс завершится в самый интересный момент
                stat = open("/proc/%d/stat" % pid, 'r')
                stats = stat.readline().split()
                stat.close()
                stat = open("/proc/%d/statm" % pid, 'r')
                stats_m = stat.readline().split()
                stat.close()
                cpu_time = (int(stats[13]) + int(stats[14])) / os.sysconf (os.sysconf_names['SC_CLK_TCK'])
                mem_usage = int(stats_m[0]) * 1024
                line = "%.3f" % (time.time() - start)
                line = line + '\b' * len(line)
                log.write(line)
                if cpu_time > self.__limit_time:
                    force_result = RunResult (RunResult.TIME_LIMIT, -1, 'cpu usage: %.2f' % cpu_time)
                    self.__process.terminate()
                if mem_usage > self.__limit_memory:
                    force_result = RunResult(RunResult.MEMORY_LIMIT, -1, 'memory usage: %d' % mem_usage)
                    self.__process.terminate()
            except IOError:
                pass
        line = "[%.3f] " % (time.time() - start)
        log.write(line)
        if force_result is not None:
            return force_result
        code = self.__process.returncode
        if code == -signal.SIGXCPU:
            return RunResult(RunResult.TIME_LIMIT, code, 'signal SIGXCPU received')
        elif code != 0:
            return RunResult(RunResult.RUNTIME, code, 'runtime error %d' % code)
        else:
            return RunResult(RunResult.OK, code)


def find_source( path ):
    global suffixes
    return heuristic.Source (suffixes).find (path)


def read_problem_properties( filename ):
  result = {}
  for line in open(filename, 'r').readlines():
    key, value = [token.strip() for token in line.split('=', 1)]
    if value[0] == '"' and value[-1] == '"':
      value = value[1:-1]
    result[key] = value
  return result

def just_run( source, stdin=None, stdout=None ):
  global configuration, log
  compiler = configuration.detect_language(source)
  if compiler is None:
    log.warning("%s: cannot detect language" % source)
    return None
  executable = compiler(source)
  if executable is None:
    log.warning("%s: compilation error" % executable)
    return None
  return executable(stdin=stdin, stdout=stdout)

def testset_answers ( problem, *, tests=None, force=False, quiet=False ):
    global log
    if problem.solution is None:
        raise t.Error ('[problem %s]: solution not found' % problem.name)
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
                log.write ('+')
            continue
        if not quiet:
            log.write('.')
        shutil.copy (test, input_name)
        r = problem.solution.run (
            directory='.temp',
            stdin=open (input_name, 'r') if type (problem.input) is Problem.File.Std else None,
            stdout=open (output_name, 'w') if type (problem.output) is Problem.File.Std else None
        )
        if not r:
            raise t.Error ('[problem %s]: solution failed on test %s.' % (problem.name, test))
        shutil.copy (output_name, test + '.a')
    if not quiet:
        log.write ('done\n')

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
    if problem.solution is None:
        log.warning('No solution defined for problem %s.' % problem.name)
    problem.cleanup ()
    generator = problem.generator
    assert generator is not None
    result = generator.run ()
    if not result:
        raise t.Error ('[problem %s]: generator failed: %s' % (problem.name, generator))
    problem.research_tests ()
    if not problem.tests:
        raise t.Error ('[problem %s]: no tests found' % problem.name)
    log('tests (total: %d): [%s]' % (len (problem.tests), ' '.join (problem.tests)))
    # TODO: convert_tests(tests), move to generation, for copy
    validator = problem.validator
    if validator is not None:
        validator.compile ()
        log('validate tests', end='')
        for test in problem.tests:
            log.write('.')
            if validator.run (test, stdin=open(test, 'r')):
                continue
            raise t.Error('[problem %s]: validation failed: %s' % (problem.name, test))
        log.write('done\n')
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
            log.error('generator (%s) failed' % self.__generator)
            return None
        return path

    @classmethod
    def file ( self, path, problem=None, name=None ):
        return Test (problem, path=path, name=name)

    @classmethod
    def generate ( self, generator, problem=None, name=None ):
        return Test (problem, generator=generator, name=name)


def check_problem ( problem, *, solution=None, tests=None, quiet=False ):
    global log
    os.chdir (problem.path)
    if tests is None:
        if not problem.tests:
            problem.research_tests ()
        tests = [Test.file (x) for x in problem.tests]
    if not tests:
        raise t.Error ('[problem %s]: no tests found' % problem.name)
    checker = problem.checker
    if checker is None:
        raise t.Error ('[problem %s]: no checker found' % problem.name)
    checker.compile ()
    if solution is None:
        solution = problem.solution
    if solution is None:
        raise t.Error ('[problem %s]: no solution found' % problem.name)
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
        limit_idle=problem.limit_idle, limit_memory=problem.limit_memory
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
            log.write ('Runtime error (%s).' % r.comment, end='\n', color=Log.ERROR)
        elif r.result == RunResult.TIME_LIMIT:
            log.write ('Time limit exceeded (%s).' % r.comment, end='\n', color=Log.ERROR)
        elif r.result == RunResult.MEMORY_LIMIT:
            log.write ('Memory limit exceeded (%s)' % r.comment, end='\n', color=Log.ERROR)
        elif r.result == RunResult.OK:
            good = True
        else:
            log.fatal ('Invokation failed (%s).' % r.comment)
        if not good:
            return False
        log.write ('* ')
        result = checker.run (input_name, output_name, test + '.a')
        if not result:
            log ('Wrong answer on test %s.' % test_name, Log.ERROR, exit=False)
            return False
    return True

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

def wolf_export( problem ):
    log.info("== upload problem %s" % configuration['id'])
    os.chdir(configuration['tests-directory'])
    if 'full' not in configuration:
        log.error("cannot full name for problem %s" % configuration['id'])
    checker = None
    for checker_name in ['check', 'checker', 'check_' + configuration['id'], 'checker_' + configuration['id']]:
        checker = find_source(os.path.join('..', checker_name))
        if checker is not None:
            break
    if checker is None:
        log.error('cannot find checker')
    wolf_compilers = {
        'delphi': 'win32.checker.delphi.ifmo',
        # 'delphi': 'win32.checker.delphi.kitten',
        'c++': 'win32.checker.c++',
        'perl': 'win32.perl' # nothing special
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
    log.write('send packets:')
    problem_id = wolf.query({'action': 'problem.create', 'name': configuration['id'], 'full': configuration['full']})
    assert isinstance(problem_id, int)
    log.write('.')
    assert wolf.query({'action': 'problem.files.set', 'id': problem_id, 'input': configuration['input-file'], 'output': configuration['output-file']})
    log.write('.')
    assert wolf.query({'action': 'problem.limits.set', 'id': problem_id, 'time': configuration['time-limit'], 'memory': configuration['memory-limit']})
    log.write('.')
    assert wolf.query({'action': 'problem.checker.set', 'id': problem_id, 'name': checker_name, 'compiler': compiler, 'source': checker})
    log.write('.')
    for test in tests:
        with open(test, 'rb') as f:
            data = f.read()
            input = base64.b64encode(data).decode('ascii')
        with open(test + '.a', 'rb') as f:
            data = f.read()
            answer = base64.b64encode(data).decode('ascii')
        assert wolf.query({'action': 'problem.test.add', 'id': problem_id, 'test': input, 'answer': answer})
        log.write('.')
    log.write('', end='\n')
    log.info('uploaded, problem id: %d' % problem_id)

def clean_problem ( problem ):
    global log, suffixes, options
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
            if re.match ('^.*\.(in|out|log|exe|dcu|ppu|o|obj|class|hi|manifest|pyc|pyo)$', filename) or \
               filename in ("input", "output"):
               os.remove (os.path.join (directory, filename))
            for suffix in suffixes:
                if not os.path.isfile (os.path.join (directory, filename + '.' + suffix)):
                    continue
                os.remove(os.path.join(directory, filename))
                break
        if remove_tests:
            cleaner = heuristic.Source.find (os.path.join (directory, 'wipe'))
            if cleaner is None:
                continue
            if not cleaner.run ():
                log.warning ('%s returned non-zero' % cleaner)
    if remove_tests and (os.path.isdir ('source') or os.path.isdir ('src')) and os.path.isdir ('tests'):
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
      0, # black
      FOREGROUND_RED, # red
      FOREGROUND_GREEN, # green
      FOREGROUND_GREEN | FOREGROUND_RED, # brown
      FOREGROUND_BLUE, # blue
      FOREGROUND_BLUE | FOREGROUND_RED, # magenta
      FOREGROUND_BLUE | FOREGROUND_GREEN, # skyblue
      FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_RED, # gray
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
    def __init__ ( self, log, configuration ):
        self.__log = self.log = log
        self.__configuration = configuration
        self.__problems = None

    def __foreach ( self, action ):
        if self.__problems is None:
            self.__explore ()
        for problem in self.__problems:
            action (problem)

    def __build ( self, problem, arguments ):
        build_problem (problem)
        if not check_problem (problem):
            raise t.Error ("problem check failed")

    def __check ( self, problem, arguments ):
        solution = None
        if len(arguments) >= 1:
            solution = heuristic.Source.find (arguments[0], problem.name_short)
            if solution is None:
                raise t.Error ("solution not found: '%s'" % arguments[0])
        check_problem (problem, solution=solution)

    def __clean ( self, problem, arguments ):
        clean_problem (problem)

    def __stress ( self, problem, arguments ):
        try:
            generator, solution = arguments[:2]
        except ValueError as error:
            raise t.Error ("usage: t.py stress <generator> <solution>") from error
        generator, solution = [heuristic.Source.find (x) for x in (generator, solution)]
        r = True
        while r:
            r = check_problem (problem, solution=solution, tests=[
                Test.generate (generator, problem=problem, name='<stress>')
            ], quiet=True )

    def __wolf_export ( self, problem, arguments ):
        problem_configuration = legacy.read_configuration (problem)
        wolf_export(problem_configuration)

    def __problem_create ( self, uuid=None ):
        problem = Problem.new ()
        uuid = problem.create (uuid)
        self.__problems = [problem]
        self.__log ('create problem #%s' % uuid)

    def __help ( self, par='disclaimer' ):
        sys.stdout.write ({
            'disclaimer': help.disclaimer,
            'gpl:c': help.license,
            'gpl:w': help.warranty,
        }[par])

    def __call__ ( self, arguments ):
        command = arguments[0]
        actions = {
            x: lambda command, args, y=y: self.__foreach (lambda problem: y (problem, args)) for x, y in [
                ('build', self.__build),
                ('check', self.__check),
                ('clean', self.__clean),
                ('stress', self.__stress),
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
            raise t.Error ("unknown command: '%s'" % command) from error
        action (command, arguments[1:])

    def __explore ( self, recursive=None ):
        if recursive is None:
            recursive = self.__configuration['recursive']
        if recursive:
            self.__problems = list (heuristic.find_problems (t=self))
        else:
            self.__problems = [heuristic.problem_open (t=self)]
        if not os.path.isdir ('.temp'):
            os.mkdir ('.temp')
        for problem in self.__problems:
           if problem.uuid is None:
              problem.create ()


def arguments_parse():
    parser = argparse.ArgumentParser (description='t.py: programming contest problem helper')
    parser.add_argument ('--no-remove-tests', '-t', dest='remove_tests', action='store_false', default=True)
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


if sys.platform == 'win32': # if os is outdated
  prepare = prepare_windows

log = Log()
configuration = Configuration()
compilers_configure()
prepare()
global_config = configuration

options, arguments = arguments_parse()

tpy = T (log, options)
try:
    if options['verbose']:
        log.verbose ()
    tpy (arguments)
except t.Error as e:
    log.error (e)
    sys.exit (1)
except KeyboardInterrupt:
    log.info ("^C")
    sys.exit (2)

