#!/usr/bin/env python3
# -*- coding: utf8 -*-

import os, re, shutil, subprocess, sys

# t.py test tool — python clone of outdated t.cmd
# version 0.03-alpha0-r1  Every time you commit modified version of t.py, increment -r<number>
# copyright (c) Oleg Davydov, Yury Petrov
# This program is free sortware, under GPL, for great justice...

# t.py is being developed in a Subversion repository with t.sh:
# https://burunduk3.geins.ru/svn/public/t.sh
# You can get latest t.py version there. And, when you make changes to t.py,
# please commit it to this repository. Ask Oleg Davydov (burunduk3@gmail.com,
# vk.com/burunduk3) if you don't have access.

# === TODO LIST ===
#  0) restore t.sh features
#  1) help
#  2) external compilers configuration

# === CHANGE LOG ===
#  2010-11-17 [burunduk3] work started



# === COMPILERS CONFIGURATION ==

class Language:
  def __init__( self, name, compile, binary=None ):
    self.name, self.binary, self.compile = name, binary, compile

class Executable:
  def __init__( self, path, command=[], add=True ):
    self.path, self.command = path, list(command)
    if add: self.command.append(self.path)
  def __str__( self ):
    return self.path
  def __call__( self, arguments=[], stdin=None, stdout=None, stderr=None ):
    process = subprocess.Popen(self.command + arguments, stdin=stdin, stdout=stdout, stderr=stderr)
    process.communicate()
    return process.returncode == 0


# Здесь начинается конфигурация компиляторов. Мерзкая штука, не правда ли?

def create_compile_default( compiler ):
  def compile_doit( source, binary, skip ):
    nonlocal compiler
    if not skip:
      t = compiler(source, binary)
      compile = subprocess.Popen(compiler(source, binary))
      compile.communicate()
      if compile.returncode != 0: return None
    return Executable(binary)
  return compile_doit

def create_compile_none( command ):
  def compile_none( source, binary, skip ):
    nonlocal command
    return Executable(source, command)
  return compile_none

def binary_default( path ):
  (path, filename) = os.path.split(path)
  if path == '': path = '.'
  return os.path.join(path, os.path.splitext(filename)[0])# + '.exe' for m$

def compile_java( source, binary, skip ):
  if not skip:
    compile = subprocess.Popen(['javac', source])
    compile.communicate()
    if compile.returncode != 0: return None
  return Executable(binary, ['java', '-Xmx256M', '-Xss128M', '-cp', os.path.dirname(binary), os.path.splitext(os.path.basename(binary))[0]], add=False)

def compile_python( source, binary, skip ):
  shabang = open(source, 'r').readline()
  if shabang[0:2] != '#!': shabang = ''
  if 'python3' in shabang: command = 'python3'
  elif 'python2' in shabang: command = 'python2'
  else: command = 'python'
  return Executable(source, [command])

include_path = '../../../include'
language = {
   'c': Language('c', create_compile_default(lambda source,binary:
       ['gcc', '-O2', '-Wall', '-Wextra', '-I', include_path, '-D__T_SH__', '-x', 'c', '-o', binary, source]), binary_default),
   'c++': Language('c++', create_compile_default(lambda source,binary:
       ['g++', '-O2', '-Wall', '-Wextra', '-I', include_path, '-D__T_SH__', '-x', 'c++', '-o', binary, source]), binary_default),
   'dpr': Language('delphi', create_compile_default(lambda source,binary:
       ['fpc', '-Mdelphi', '-O3', '-FE.', '-v0ewn', '-Sd', '-Fu' + include_path, '-Fi' + include_path, '-d__T_SH__', '-o'+binary, source]), binary_default),
   'java': Language('java', compile_java, lambda path: os.path.splitext(path)[0] + '.class'),
   'pas': Language('pascal', create_compile_default(lambda source,binary:
       ['fpc', '-O3', '-FE.', '-v0ewn', '-Sd', '-Fu' + include_path, '-Fi' + include_path, '-d__T_SH__', '-o'+binary, source]), binary_default),
   'pl': Language('perl', create_compile_none(['perl'])),
   'py': Language('python', compile_python),
   'sh': Language('bash', create_compile_none(['bash']))
}
for suffix in ['cpp', 'cxx', 'C']: language[suffix] = language['c++'] # additional c++ suffixes
suffixes = language.keys()



# === PARTS OF t.sh ===

#scriptName=`basename $0`
#INCLUDE_PATH="../../../include"

#OPERATION_SYSTEM=`uname || echo 'system_error'` # Windows is system error ^_~

## GCC flags
#gccVersionString=`gcc --version | head -n 1`
#gccVersion=${gccVersionString##* }
#gccVersionMajor=${gccVersion##*.}
#if [ $gccVersionMajor == "4" ] ; then
#  CFLAGS="-O2 -Wall -Wextra -I $INCLUDE_PATH -D__T_SH__"
#else
#  CFLAGS="-O2 -Wall -I $INCLUDE_PATH -D__T_SH__"
#fi
#CXXFLAGS="${CFLAGS}"
## End of GCC flags

#FPCFLAGS="-O3 -FE. -v0ewn -Sd -Fu$INCLUDE_PATH -Fi$INCLUDE_PATH -d__T_SH__"
#JAVAFLAGS="-Xmx256M -Xss128M"
#BINARY_SUFFIX=""
#if [ "$OPERATION_SYSTEM" != "Linux" ]; then
#  CFLAGS="$CFLAGS -Wl,--stack=134217728"
#  CXXFLAGS="$CXXFLAGS -Wl,--stack=134217728"
#  BINARY_SUFFIX=".exe"
#fi

class Log:
  DEBUG = 1
  INFO = 2
  NOTICE = 3
  WARNING = 4
  ERROR = 5
  FATAL = 6
  def __init__( self ):
    self.color = {Log.DEBUG: 37, Log.INFO: 36, Log.NOTICE: 32, Log.WARNING: 33, Log.ERROR: 31, Log.FATAL: 31}
    self.message = {Log.DEBUG: 'debug', Log.INFO: 'info', Log.NOTICE: 'notice', Log.WARNING: 'warning', Log.ERROR: 'error', Log.FATAL: 'fatal error'}
    self.debug = lambda text: self(text, Log.DEBUG)
    self.info = lambda text: self(text, Log.INFO)
    self.notice = lambda text: self(text, Log.NOTICE)
    self.warning = lambda text: self(text, Log.WARNING)
    self.error = lambda text: self(text, Log.ERROR)
    self.fatal = lambda text: self(text, Log.FATAL)
    pass
  def __call__( self, message, level = INFO, exit=None, end='\n' ):
    self.write("[t:%s] \x1b[1;%dm%s\x1b[0m" % (self.message[level], self.color[level], message), end=end)
    exit = exit if exit is not None else level >= Log.ERROR
    if exit: sys.exit(1)
  def write( self, message, end='' ):
    print(message, end=end)
    sys.stdout.flush()


def find_problems( base = '.' ):
  queue = [os.path.abspath(base)]
  for path in queue:
    if not os.path.isdir(path): continue;
    if os.path.exists(os.path.join(path, 'tests')) or os.path.exists(os.path.join(path, 'source')) or os.path.exists(os.path.join(path, 'src')):
      yield path
    else:
      queue += [os.path.join(path, x) for x in sorted(os.listdir(path))]

def find_source( path ):
  global suffixes
  for filename in [path + '.' + suffix for suffix in suffixes]:
    if os.path.isfile(filename):
      return filename
  if os.path.isfile(path):
    return path
  return None

def find_tests( path = '.' ):
  for filename in sorted(os.listdir(path)):
    if not re.match('^\d{2,3}$', filename): continue
    if not os.path.isfile(os.path.join(path, filename)): continue
    yield filename

def find_solution( path, token, problem ):
  result = find_source(os.path.join(path, token))
  if result is not None: return result
  result = find_source(os.path.join(path, problem + '_' + token))
  if result is not None: return result
  # В t.sh был ещё один случай: когда мы выбираем файл c именем <problem>_<token>, но не делаем find_source.
  # Я пока не буду это здесь повторять, потому что не могу придумать случай, когда это нужно.
  return None

class Source:
  def __init__( self, path, lang = None ):
    global language
    if lang is None:
      lang = language[os.path.splitext(path)[-1][1:]]
    self.path, self.language = path, lang
  def binary( self ):
    return self.language.binary(self.path) if self.language.binary is not None else self.path
  def compile( self ):
    global log
    binary, skip = self.binary(), False
    if binary == self.path or (os.path.isfile(binary) and os.stat(binary).st_mtime >= os.stat(self.path).st_mtime):
      log('compile skipped: %s' % binary)
      skip = True
    else:
      log('compile: %s -> %s' % (self.path, binary))
    return self.language.compile(self.path, binary, skip)


def read_problem_properties( filename ):
  result = {}
  for line in open(filename, 'r').readlines():
    line = [token.strip() for token in line.split('=', 1)]
    if len(line) != 2: continue
    result[line[0]] = line[1]
  return result

def read_configuration( path ):
  problem_name = os.path.basename(os.path.abspath(path))
  configuration = {'path': path, 'name': problem_name}
  configuration.update({'input-file': problem_name + '.in'})
  configuration.update({'output-file': problem_name + '.out'})
  for directory in ['source', 'src', 'tests']:
    if os.path.isdir(os.path.join(path, directory)):
      configuration.update({'source-directory': os.path.join(path, directory)})
      break
  configuration.update({'tests-directory': os.path.join(path, 'tests')})
  ppfile = os.path.join(path, 'problem.properties')
  if os.path.isfile(ppfile):
    configuration.update(read_problem_properties(ppfile))
  #configuration.update(configuration_force)
  return configuration

def convert_tests( tests ):
  log('convert tests', end='')
  for test in tests:
    log.write('.')
    p = subprocess.Popen(['dos2unix', test], stderr=open('/dev/null', 'w'))
    p.communicate()
    if p.returncode != 0: log.warning('dos2unix failed on test %s' % test)
    if not os.path.isfile(test + '.a'):
      continue
    p = subprocess.Popen(['dos2unix', test + '.a'], stderr=open('/dev/null', 'w'))
    p.communicate()
    if p.returncode != 0: log.warning('dos2unix failed on file %s.a' % test)
  log.write('done\n')

def build_problem( configuration ):
  global log
  path = configuration['path']
  problem_name = configuration['name']
  log('== building problem “%s” ==' % problem_name)
  config_names = {'path': 'problem path', 'solution': 'default solution', 'source-directory': 'source directory', 'input-file': 'input file', 'output-file': 'output file'}
  for key in sorted(configuration.keys()):
    name = config_names[key] if key in config_names else ('“%s”' % key)
    log('  * %s: %s' % (name, configuration[key]))
  if 'solution' not in configuration: log.warning('No solution defined for problem %s.' % problem_name)
  if 'source-directory' not in configuration: log.error('No source directory defined for problem %s.' % problem_name)
  os.chdir(path)
  # cleanup
  if os.path.isdir(configuration['tests-directory']):
    for filename in os.listdir(configuration['tests-directory']):
      if re.match('^\d{2,3}(\.a)?$', filename):
        os.remove(os.path.join(configuration['tests-directory'], filename))
  else:
    os.mkdir(configuration['tests-directory'])
  #
  os.chdir(configuration['source-directory'])
  doall = find_source('doall')
  if doall is not None:
    log('using generator: %s' % doall)
    result = Source(doall).compile()()
    if not result: log.error('generator failed')
  else:
    log('auto-generating tests')
    count_hand, count_gen = 0, 0
    for test in ['%02d' % i for i in range(100)]:
      target = os.path.join(configuration['tests-directory'], test)
      if os.path.isfile(test + '.hand'):
        shutil.copy(test + '.hand', target)
        count_hand += 1
      elif os.path.isfile(test + '.manual'):
        shutil.copy(test + '.manual', target)
        count_hand += 1
      else:
        generator = find_source('do' + test)
        generator = find_source('gen' + test) if generator is None else generator
        if generator is None: continue
        result = Source(generator).compile()(stdout=open(target, 'w'))
        if not result: log.error('generator (%s) failed' % generator)
        count_gen += 1
    if count_hand != 0: log('manual tests copied: %d' % count_hand)
    if count_gen != 0: log('generated tests: %d' % count_gen)
  tests = list(find_tests(configuration['tests-directory']))
  if not tests: log.error('no tests found in %s' % configuration['tests-directory'])
  log('tests (total: %d): %s' % (len(tests), ','.join(tests)))
  os.chdir(configuration['tests-directory'])
  convert_tests(tests)
  validator = None
  for name in ['validate', 'validator']:
    validator = find_source(os.path.join(configuration['source-directory'], name))
    if validator is not None: break
  if validator is not None:
    validator = Source(validator).compile()
    log('validate tests', end='')
    for test in tests:
      log.write('.')
      if validator(arguments=[test], stdin=open(test, 'r')): continue
      log.error('Test %s failed validation.' % test)
    log.write('done\n')
  solution = find_solution(path, configuration['solution'], problem_name) if 'solution' in configuration else None
  if solution is None:
    log.warning('Solution not found.')
    return False
  #log('path=%s, solution=%s' % (path, solution), Log.DEBUG)
  solution = Source(os.path.join(path, solution)).compile()
  log('generate answers', end='')
  input_name, output_name = configuration['input-file'], configuration['output-file']
  input_name = problem_name + '.in' if input_name == '<stdin>' else input_name
  output_name = problem_name + '.out' if output_name == '<stdout>' else output_name
  for test in tests:
    if os.path.isfile(test + '.a'):
      log.write('+')
      continue
    log.write('.')
    shutil.copy(test, input_name)
    r = solution(stdin=open(input_name, 'r') if configuration['input-file'] == '<stdin>' else None, stdout=open(output_name, 'w') if configuration['output-file'] == '<stdout>' else None)
    if not r: log.error('Solution failed on test %s.' % test)
    shutil.copy(output_name, test + '.a')
  log.write('done\n')
  return True


def check_problem( configuration, solution=None ):
  problem_name = configuration['name']
  os.chdir(configuration['tests-directory'])
  tests = list(find_tests(configuration['tests-directory']))
  if not tests:
    log.warning('No tests found for problem %s.' % problem_name)
    return False
  checker = None
  for checker_name in ['check', 'checker', 'check_' + problem_name, 'checker_' + problem_name]:
    checker = find_source(os.path.join('..', checker_name))
    if checker is not None: break
  if checker is None:
    log.warning('Checker wasn\'t found, solution wouldn\'t be checked.')
    return False
  checker = Source(checker).compile()
  if checker is None:
    log.warning('Checker: compilation error.')
    return False
  solution_name = configuration['solution'] if solution is None else solution
  solution = find_solution(configuration['path'], solution_name, problem_name)
  if solution is None:
    log.warning('Solution (%s) wasn\'t found.' % solution_name)
    return False
  solution = Source(solution).compile()
  if solution is None:
    log.warning('Solution (%s): compilation error.' % solution_name)
    return False
  log.info('checking solution: %s' % solution)
  input_name, output_name = configuration['input-file'], configuration['output-file']
  input_name = problem_name + '.in' if input_name == '<stdin>' else input_name
  output_name = problem_name + '.out' if output_name == '<stdout>' else output_name
  for test in tests:
    log('test [%s] ' % test, Log.INFO, end='')
    shutil.copy(test, input_name)
    r = solution(stdin=open(input_name, 'r') if configuration['input-file'] == '<stdin>' else None, stdout=open(output_name, 'w') if configuration['output-file'] == '<stdout>' else None)
    if not r: log.error('Solution failed on test %s.' % test)
    result = checker(arguments=[input_name, output_name, test + '.a'])
    if not result: log.error('Wrong answer on test %s.' % test)
  return True


def clean_problem( path ):
  global suffixes, options
  os.chdir(path)
  remove_tests = 'no-remove-tests' not in options or not options['no-remove-tests']
  if remove_tests and os.path.isdir('tests'):
    for filename in os.listdir('tests'):
      if not re.match('^\d{2,3}(.a)?$', filename): continue
      os.remove(os.path.join('tests', filename))
  if os.path.isfile(os.path.join('tests', 'tests.gen')): os.remove(os.path.join('tests', 'tests.gen'))
  for directory in ['.', 'tests', 'src', 'source']:
    if not os.path.isdir(directory): continue
    for filename in os.listdir(directory):
      if re.search('\.(in|out|log|exe|dcu|ppu|o|obj|class|hi|manifest|pyc|pyo)$', filename):
        os.remove(os.path.join(directory, filename))
      for suffix in suffixes:
        if not os.path.isfile(os.path.join(directory, filename + '.' + suffix)): continue
        os.remove(os.path.join(directory, filename))
        break
    if remove_tests:
      cleaner_name = find_source(os.path.join(directory, 'wipe'))
      if cleaner_name is None: continue
      cleaner = Source(cleaner_name).compile()
      if cleaner is None:
        log.warning('Compilation failed: %s.' % cleaner_name)
        continue
      result = cleaner()
      if not result:
        log.warning('%s returned non-zero' % cleaner)
  if remove_tests and (os.path.isdir('source') or os.path.isdir('src')) and os.path.isdir('tests'):
    os.rmdir('tests')

log = Log()

if sys.platform == 'win32': # if os is outdated
  # Это выглядит как мерзкий, грязный хак, каковым является вообще любая работа с windows.
  import ctypes

  STD_INPUT_HANDLE = -10
  STD_OUTPUT_HANDLE= -11
  STD_ERROR_HANDLE = -12

  FOREGROUND_BLUE = 0x01
  FOREGROUND_GREEN= 0x02
  FOREGROUND_RED  = 0x04
  FOREGROUND_INTENSITY = 0x08
  BACKGROUND_BLUE = 0x10
  BACKGROUND_GREEN= 0x20
  BACKGROUND_RED  = 0x40
  BACKGROUND_INTENSITY = 0x80
  windows_colors = [
    0, # black
    FOREGROUND_RED, # red
    FOREGROUND_GREEN, #green
    FOREGROUND_GREEN|FOREGROUND_RED, # brown
    FOREGROUND_BLUE, # blue
    FOREGROUND_BLUE|FOREGROUND_RED, # magenta
    FOREGROUND_BLUE|FOREGROUND_GREEN, # skyblue
    FOREGROUND_BLUE|FOREGROUND_GREEN|FOREGROUND_RED, # gray
    0,0,0
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
        if x == 0: mask |= windows_colors[7]
        if x == 1: mask |= FOREGROUND_INTENSITY
        if 30 <= x <= 39: mask |= windows_colors[x - 30]
      ctypes.windll.kernel32.SetConsoleTextAttribute(handle, mask)
      sys.stdout.write(line.encode('utf8').decode('ibm866'))
      sys.stdout.flush()
  def windows_convert_tests( tests ):
    pass
  log.write = windows_write
  convert_tests = windows_convert_tests

log.warning('t.py isn\'t finished yet, only basic features are availible')

arguments, arguments_force = [], False
options = {}
for arg in sys.argv[1:]:
  if len(arg) >= 1 and arg[0] == '-' and not arguments_force:
    if len(arg) >= 2 and arg[1] == '-':
      if arg == '--': arguments_force = True
      elif arg == '--no-remove-tests': options['no-remove-tests'] = True
      else:
        pass
    else:
      for option in arg[1:]:
        if option == 't': options['no-remove-tests'] = True
        else:
          pass
  else:
    arguments.append(arg)
command = arguments[0] if len(arguments) > 0 else None

if command == 'build':
  for problem in find_problems():
    configuration = read_configuration(problem)
    build_problem(configuration)
    check_problem(configuration)
elif command == 'check':
  for problem in find_problems():
    configuration = read_configuration(problem)
    if len(arguments) > 1:
      configuration['solution'] = arguments[1]
    check_problem(configuration)
elif command == 'clean':
  for problem in find_problems():
    clean_problem(problem)


