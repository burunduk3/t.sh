#!/bin/bash

# t.sh test tool — clone of outdated t.cmd
# version 0.02-alpha0-r12  Every time you commit modified version of t.sh, increment -r<number>
# copyright (c) Oleg Davydov, Yury Petrov
# This program is free sortware, under GPL, for great justice...

# t.sh is being developed in a Subversion repository:
# https://burunduk3.geins.ru/svn/public/t.sh
# You can get latest t.sh version there. And, when you make changes to t.sh,
# please commit it to this repository. Ask Oleg Davydov (burunduk3@gmail.com,
# vk.com/burunduk3) if you don't have access.

# questions
#   1. If there is directory “tests”, shall we recursive scan into subdirectories?
#   2. If there is directory “src”, should “clean” command remove “tests” directory? yes

# todo
#   1. Parameters for running java and compiling all
#   2. [echo_colored] support for -n [done]
#   3. Advanced coloring
#   4. Standard input/output (option?)
#   5. Replace printf "%02d" $i (ex-seq...) with something even more appropriate.
#      (I suppose grepping smth like [0-9]{2-3} and so on. -- Yury Petrov)
#   6. Add statistics (using time?)
#   7. t.sh check xx --allow-wa [done]
#   8. Kill if TL (ulimit)
#   9. Rewrite clean: do not remove files that don't have to be removed.
#      Store list of files created during build in smth like .t.sh.list
#      using a kind of diff of ls's before and after.

# changelog
#   1. 2009-11-06: src directory support
#   2. 39-312 (2009-11-09): perl support, doall-generated answers support
#   3. 2009-11-17: seq -> printf
#   4. 2009-11-20: -D__T_SH__
#   5. 40-034 (20010-02-04): added compile skipping (like make)
#   6. 2010-06-08: Python & bash support
#   7. 2010-06-21: Some help; -t as an alias for --no-remove-tests;
#      doall is handled in a more common way
#   8. 2010-06-24: Help about clean, minor fixes
#   9. 40-178 (2010-06-28): better argument parsing
#      added --allow-wa
#  10. 2010-07-18: Java path bugfix
#  11. 40-248 (2010-09-06) compile system upgrade

#name=`stat "$0" --format '%n'`
#while [[ `stat "$name" --format '%F'` == 'symbolic link' ]]; do
#  name=`stat "$name" --format '%N' | sed -e $'s/^\`[^\']*\' -\> \`\\([^\']*\\)\'/\\1/'`
#done
#echo "nane = $name"
#echo "${0%/*}/"


scriptName=`basename $0`
INCLUDE_PATH="../../../include"

OPERATION_SYSTEM=`uname || echo 'system_error'` # Windows is system error ^_~

# GCC flags
gccVersionString=`gcc --version | head -n 1`
gccVersion=${gccVersionString##* }
gccVersionMajor=${gccVersion##*.}
if [ $gccVersionMajor == "4" ] ; then
  CFLAGS="-O2 -Wall -Wextra -I $INCLUDE_PATH -D__T_SH__"
else
  CFLAGS="-O2 -Wall -I $INCLUDE_PATH -D__T_SH__"
fi
CXXFLAGS="${CFLAGS}"
# End of GCC flags

FPCFLAGS="-O3 -FE. -v0ewn -Sd -Fu$INCLUDE_PATH -Fi$INCLUDE_PATH -d__T_SH__"
JAVAFLAGS="-Xmx256M -Xss128M"
BINARY_SUFFIX=""
if [ "$OPERATION_SYSTEM" != "Linux" ]; then
  CFLAGS="$CFLAGS -Wl,--stack=134217728"
  CXXFLAGS="$CXXFLAGS -Wl,--stack=134217728"
  BINARY_SUFFIX=".exe"
fi

# === help messages ===

function help_build()
{
  echo "build: create tests, validate, generate answers, check"
  echo "  First, t.sh recursively searches directory tree for the problems."
  echo "  A directory is considered to look like a problem iff it contains"
  echo "  either “src”, “source” or “tests” subdirectory."
  echo "  For each problem directory found, the following procedure is executed:"
  echo "  Step 0: First existing directory in order “source”, “src”, “tests”"
  echo "    is the source directory."
  echo "  *Note: <test> stands for any (or every) string of 2–3 digits."
  echo "  Step 1: generate tests"
  echo "    t.sh searches the source directory for doall.sh, then for doall.cmd or doall.bat."

  echo "    If none of above has been found, t.sh tries to generate each test separately,"
  echo "    using “do<test>.*” files or just copying “<test>.hand” or “<test>.manual” files."
  echo "  Step 2: validate tests"
  echo "    TODO: validate process"
  echo "    If no validator was found, the step is skipped with a warning"
  echo "  Step 3: generate answers"
  echo "    If exact solution was specified, it is used. Otherwise, file t.sh greps the"
  echo "    “problem.properties” file for a string “solution” and tries to use it."
  echo "    Then t.sh runs the solution on every test and copies resulting files to “<test>.a”"
  echo "  Step 4: check"
  echo "    If some checker is present (a program named “check”, “checker”, “check_<problem>”),"
  echo "    the model solution is run on every test and checked using that checker."
}

function help_build()
{
  echo "clean: remove stuff created during build/check/etc"
  echo "  Parameters:"
  echo "    --no-remove-tests (-t): do not remove tests created by t.sh"
  echo "  Note: this command might might do something that you do not expect as it"
  echo "  uses heuristics to determine files for removal. In a problem directory"
  echo "  for each source file recognised t.sh will remove file that it would expect"
  echo "  to be the result of its compilation. Second, the “tests” directory wiil be"
  echo "  removed, if no --no-remove-tests option was specified."
}

function help_common()
{
  # some useful info
  #  — enviropment variable COLOR_DISABLE disables coloring output when set to “true”
  echo "TODO: help common"
}

function help_usage()
{
  echo "t.sh is a test management tool"
  echo "Usage: t.sh build|check|clean|help [<options>]"
  echo "  build — build all problems in current firectory (generate & validate tests,"
  echo "          generate answers."
  echo "  check — check a solution."
  echo "  clean — cleanup everything created by a run of build"
  echo "  help — display more detailed help on a command"
}



# echo_colored: outputs one-line colored message
#   usage: echo_colored <color> <message>
#   color should be in vt100 style (for example, “1;31” means bold red)
#   COLOR_* consants can be used
#   variable COLOR_DISABLE disables coloring when equals to “true”
function echo_colored() {
  if [ "$COLOR_DISABLE" == 'true' ]; then
    echo "${*:2}"
  else
    echo $'\e['"$1"'m'"${*:2}"$'\e[0m'
  fi
}
COLOR_RED="1;31"
COLOR_GREEN="1;32"
COLOR_YELLOW="1;33"
COLOR_WHITE="1;37"
COLOR_BLUE="1;34"
COLOR_PURPLE="1;35"
COLOR_CYAN="1;36"
COLOR_DISABLE='false'

# tsh_message: print message and exits if out to be so.
#   usage: tsh_message [-n] <message-type> <message> [<exit-flag>]
#     -n flag means no line break after output
#     exit flag should be “fatal” or “non-fatal”, “fatal” means exiting
#     default value of exit flag depends on error type, “fatal“ and “error” types exits
#     error type can be one of following values:
#       fatal — means that there was error and there is no way to continue t.sh
#       error — means error that can be ignored but behviour of t.sh is undefined since it
#       warning — means error that can be ignored in most cases, otherwise t.sh will generate stronger error later
#       notice — means something
#       message — general output message
#       debug — means information that was used for debugging. This should not appear in final version of t.sh
#     theese types are displayed with different colors ^_~
typeset -A MESSAGE_COLOR
MESSAGE_COLOR['fatal']="$COLOR_RED"
MESSAGE_COLOR['error']="$COLOR_RED"
MESSAGE_COLOR['warning']="$COLOR_YELLOW"
MESSAGE_COLOR['notice']="$COLOR_GREEN"
MESSAGE_COLOR['message']="$COLOR_CYAN"
MESSAGE_COLOR['debug']="$COLOR_WHITE"
function tsh_message()
{
  lineBreak="true"
  if [ "$1" == "-n" ]; then
    lineBreak="false"
    shift
  fi
  errorType="$1"
  text="$(echo_colored "${MESSAGE_COLOR[$1]}" "[$scriptName, $errorType]" "$2")"
  if [ "$lineBreak" == 'false' ]; then
    echo -n "$text"
  else
    echo "$text"
  fi
  if [ "$1" == 'warning' ] || [ "$1" == 'notice' ] || [ "$1" == 'message' ] || [ "$1" == 'debug' ]; then
    exitFlag='non-fatal'
  else
    exitFlag='fatal'
  fi
  if [ ${#*} == 3 ]; then
    exitFlag="$3"
  fi
  case "$exitFlag" in
    ('fatal') exit 239;;
    ('non-fatal') return;;
    (*) echo_colored $COLOR_RED "[$scriptName, internal error]" "incorrect exit flag “$exitFlag”";;
  esac
}


# === find functions === 

# find_recursive function — function for dive into directory tree
#   usage: find_recursive <directory>
#     <directory> is directory to start from
#   when it finds directory looks like directory with problem (see help directories)
#   it adds directory to global variable named “result“ which should be an array
function find_recursive()
{
  for i in 'source' 'src' 'tests'; do
    if [ -d "$1/$i" ]; then
      result[${#result[*]}]="$1"
      return 0
    fi
  done
  for i in "$1"/*; do
    if [ -d "$i" ]; then
      find_recursive $i
    fi
  done
}

# find_problem — function for scanning directory tree in search for problems
#   usage: find_problem <start-directory>
#   outcome is variable “result” — array of directories with problems
function find_problem()
{
  result=()
  directory="$1"
  if [ ! -d "${directory}" ]; then
    tsh_message "error" "[recursive_problem] directory “$directory” doesn't looks like directory"
    return
  fi
  find_recursive "$directory"
}

# find_source — function for location source file with unknown sufix
#   usage: find_source <prefix>
#     prefix is file name without “.<suffix>”, where suffix depends on source language
#     c — C source
#     cpp — C++ source
#     dpr,pas — Free Pascal source
#     java — Java source
#   returns zero (true) iff found
#   if found also returns suffix in “result” global variable
function find_source()
{
  for test_source_i in c cpp c++ dpr java pas pl py sh; do
    if [ -f "$1.$test_source_i" ]; then
      result="$test_source_i"
      return 0
    fi
  done
  return 1 
}

# find_solution — function for location solution with given flag
#   usage: find_solution <directory> <specification> <problem-name>
#   exact solution file (without directory) will be saved in global variable “result”
#   see help solutions for details
#   returns zero (true) iff found
#   if found also returns full solution name in “result” glabal variable
function find_solution()
{
  solutionDirectory="$1"
  solutionSuffix="$2"
  problemName="$3"
  if [ -f "${solutionDirectory}${solutionSuffix}" ]; then
    result="$solutionSuffix"
    return 0
  elif find_source "${solutionDirectory}${problemName}_${solutionSuffix}"; then
    result="${problemName}_${solutionSuffix}.${result}"
    return 0
  elif [ -f "${solutionDirectory}${problemName}_${solutionSuffix}" ]; then
    result="${problemName}_${solutionSuffix}"
    return 0
  else
    return 1;
  fi
}

# language — returns language from suffix
function language() {
  case "$1" in
    ('C') echo 'c++' ;;
    ('c') echo 'c' ;;
    ('cpp') echo 'c++' ;;
    ('c++') echo 'c++' ;;
    ('dpr') echo 'delphi' ;;
    ('java') echo 'java' ;;
    ('pas') echo 'pascal' ;;
    ('pl') echo 'perl' ;;
    ('py') echo 'python' ;;
    ('sh') echo 'bash' ;;
  esac
}

# === source functions ===

# source_compile <sourceFile> <language> [<targetFile>]
#   Function for preparing source file to be executed. For some languages that means compiling file
#   into an executable. By now, language can be one of:
#     bash — bash script, will be executed using bash
#     c — C source, will be compiled using gcc
#     c++ — C++ source, will be compiled using g++
#     delphi — delphi source, will be compiled using fpc -Mdelphi
#     java — java source, will be compiled using javac
#     pascal — pascal source, will be compiled using fpc
#     perl — perl script, will be executed using perl
#     python — python scipt, will be executed using python, python2 or python3 depending on file sha-bang (if any)
#   Some languages (c, c++, dpr and pas) support changing target binary (or class) file name using targetFile parameter.
#   Function returns execution command, it can be later appended with parameters and/or redirections.
function source_compile()
{
  sourceFile="$1"
  language="$2"
  case "$language" in
    ('bash')
      echo "bash '$sourceFile'"
    ;;
    ('c')
      targetFile="${3:-$(echo "$sourceFile" | sed -e 's/\.c$/'$BINARY_SUFFIX'/')}"
      compileCommand="gcc $CFLAGS -o '$targetFile' -x c '$sourceFile'"
      echo "'./$targetFile'"
    ;;
    ('c++')
      targetFile="${3:-$(echo "$sourceFile" | sed -e 's/\.\(C\|cpp\|cxx\|c++\)$/'$BINARY_SUFFIX'/')}"
      compileCommand="g++ $CXXFLAGS -o '$targetFile' -x c++ '$sourceFile'"
      echo "'./$targetFile'"
    ;;
    ('delphi')
      targetFile="${3:-$(echo "$sourceFile" | sed -e 's/\.dpr$/'$BINARY_SUFFIX'/')}"
      compileCommand="fpc -Mdelphi $FPCFLAGS -o'$targetFile' '$sourceFile'"
      echo "'./$targetFile'"
    ;;
    ('java')
      classPath="`echo "./$sourceFile" | sed -e 's/\/[^\/]*$//'`"
      className="`echo "./$sourceFile" | sed -e 's/^.*\/\([^\/]*\)\.java$/\1/'`"
      targetFile="$(echo "$sourceFile" | sed -e 's/\.java$/.class/')"
      compileCommand="javac '$sourceFile'"
      echo "java $JAVAFLAGS -cp '$classPath' '$className'"
    ;;
    ('pascal')
      targetFile="${3:-$(echo "$sourceFile" | sed -e 's/\.pas$/'$BINARY_SUFFIX'/')}"
      compileCommand="fpc $FPCFLAGS -o'$targetFile' '$sourceFile'"
      echo "'./$targetFile'"
    ;;
    ('perl')
      echo "perl '$sourceFile'"
    ;;
    ('python')
      if head "$sourceFile" --lines=1 | grep -P '^#!.*python3' > /dev/null ; then
        python="python3"
      elif head "$sourceFile" --lines=1 | grep -P '^#!.*python2' > /dev/null ; then
        python="python3"
      else
        python="python"
      fi
      echo "$python '$sourceFile'"
    ;;
    (*) tsh_message 'error' "unknown language (“$language”)" 1>& 2;;
  esac
  if [ "$compileCommand" == "" ]; then
    return;
  fi
  if [ "$sourceFile" -nt "$targetFile" ]; then
    tsh_message 'message' "$compileCommand" 1>&2
    bash -c "$compileCommand" 1>&2 || tsh_message 'error' "compile failed" 1>&2
  else
    tsh_message 'message' "compile($sourceFile) skipped" 1>&2
  fi
}

# source_run — function for running program using one of standart schemes
#   usage: solution_run <runCommand> [<input-file> [<output-file>]]
#   currently there are 2 schemes that differs from others: java and perl
#   if <output-file> is set, standart output of program is redirected to it
# TODO: better input/output redirect handling
function source_run()
{
  runCommand="$1"
  inputFile="$2"
  outputFile="$3"
  if [ "$inputFile" == "" ]; then
    if [ "$outputFile" == "" ]; then
      bash -c "$runCommand ${*:4}" || return 1
    else
      bash -c "$runCommand ${*:4}" > "$outputFile" || return 1
    fi
  else
    if [ "$outputFile" == "" ]; then
      bash -c "$runCommand ${*:4}" < "$inputFile" || return 1
    else
      bash -c "$runCommand ${*:4}" < "$inputFile" > "$outputFile" || return 1
    fi
  fi
}


#...

function find_tests()
{
  result=()
  for file in [0-9][0-9]{,[0-9]}; do
    if [ -f $file ]; then
      result[${#result[*]}]="$file";
    fi
  done
}

tests=()

function do_check()
{
  problemName="$1"
  solution="$2"
  checkerName=""
  for checkName in "../check" "../checker" "../checker_$problemName"; do
    if find_source "$checkName"; then
      checkerName="$checkName.$result"
      checkerLanguage="$(language "$result")"
      break
    fi
  done
  if [ "$checkerName" == "" ]; then
    tsh_message "warning" "checker not found, solution wouldn't be checked"
    return 1
  fi
  checker="$(source_compile "$checkerName" "$checkerLanguage")"
  #tsh_message 'debug' "checker: “$checker”"
  tsh_message 'message' "checking solution"
  checkerError='error'
  if [ "$arg_AllowWA" == 'true' ]; then
    checkerError='warning'
  fi
  for testNumber in ${tests[*]}; do
    tsh_message -n "message" "test [$testNumber] "
    cp "$testNumber" "$pInputFileName"
    if [ "$pInputFile" == "<stdin>" ]; then
      inputFile="$pInputFileName";
    else
      inputFile=""
    fi
    if [ "$pOutputFile" == "<stdout>" ]; then
      outputFile="$pOutputFileName";
    else
      outputFile=""
    fi
    source_run "$solution" "$inputFile" "$outputFile" || tsh_message "error" "solution failed on test [$testNumber]"
    source_run "$checker" "" "" "$testNumber" "$pOutputFileName" "$testNumber.a" || tsh_message "$checkerError" "check failed on test [$testNumber]"
  done
  rm --force "$problemName."{in,out}
}

# ...


# ...

function readProblemProperties()
{
  if [ -f "$problemDirectory/problem.properties" ]; then
    pSolution=`cat "$problemDirectory/problem.properties" | grep "solution" | sed -e 's/^solution *= *//'`
    pInputFile=`cat "$problemDirectory/problem.properties" | grep "input-file" | sed -e 's/^input-file *= *//'`
    pOutputFile=`cat "$problemDirectory/problem.properties" | grep "output-file" | sed -e 's/^output-file *= *//'`
  fi
  if [ "$pInputFile" == "" ]; then # default value of input-file
    pInputFile="$problemName.in"
  fi
  if [ "$pOutputFile" == "" ]; then # default value of output-file
    pOutputFile="$problemName.out"
  fi
  if [ "$pInputFile" == "<stdin>" ]; then
    pInputFileName="$problemName.in"
  else
    pInputFileName="$pInputFile"
  fi
  if [ "$pOutputFile" == "<stdout>" ]; then
    pOutputFileName="$problemName.out"
  else
    pOutputFileName="$pOutputFile"
  fi
}

# t.sh commands


# t.sh commands

t_build()
{
  find_problem "`pwd`"
  problems=(${result[*]});
  for (( currentProblem = 0; currentProblem < ${#problems[*]}; currentProblem++ )); do
    problemDirectory="${problems[$currentProblem]}"
    problemName="`echo "$problemDirectory" | sed -e 's/^.*[\/.]\([^\/.]*\)$/\1/'`"
    tsh_message "message" "=== working with problem “$problemName” ==="
    readProblemProperties
    tsh_message "message" " * directory: $problemDirectory"
    tsh_message "message" " * input: $pInputFile"
    tsh_message "message" " * output: $pOutputFile"
    if [ "$pSolution" == "" ]; then
      tsh_message "warning" " * solution isn't defined"
    else
      tsh_message "message" " * solution: $pSolution"
    fi
    pSolutionSuffix=""
    if [ "$pSolution" != "" ]; then
      pSolutionSuffix="$pSolution"
    fi
    if [ "${tParameters[1]}" != '' ]; then
      pSolutionSuffix="${tParameters[1]}"
    fi

    sourceDirectory=""
    for i in 'source' 'src' 'tests'; do
      if [ -d "$problemDirectory/$i" ]; then
        sourceDirectory="$problemDirectory/$i"
        break;
      fi
    done

    testsDirectory="$problemDirectory/tests"

    pushd "$sourceDirectory" > /dev/null 2>&1
    # clean:
    if [ -d $testsDirectory ]; then
      rm --force "$testsDirectory"/[0-9][0-9]{,[0-9]}{,.a} || tsh_message "fatal" "rm failed"
    else
      mkdir "$testsDirectory" || tsh_message "fatal" "mkdir failed"
    fi

    # run scripts:
    if find_source "doall" ; then
      doSuffix="$result"
      doall="$(source_compile "doall.$doSuffix" "$(language "$doSuffix")")"
      source_run "$doall"  || tsh_message "error" "doall.sh failed"
    else
      counterHand="0";
      counterDo="0";
      for (( __j = 0; __j < 100; __j++ )) ; do
        j=`printf "%02d" $__j`
        if [ -f "$j.hand" ]; then
          counterHand=$(($counterHand + 1))
          cp "$j.hand" "$testsDirectory/$j"
        elif [ -f "$j.manual" ]; then
          counterHand=$(($counterHand + 1))
          cp "$j.manual" "$testsDirectory/$j"
        elif find_source "do$j"; then
          counterDo=$(($counterDo + 1))
          doSuffix="$result"
          dodo="$(source_compile "do$j.$doSuffix" "$(language "$doSuffix")")"
          source_run "$dodo" "" "$testsDirectory/$j"
        elif find_source "gen$j"; then
          counterDo=$(($counterDo + 1))
          doSuffix="$result"
          dodo="$(source_compile "gen$j.$doSuffix" "$(language "$doSuffix")")"
          source_run "$dodo" "" "$testsDirectory/$j"
        fi
      done
      if ! [ "$counterHand" == "0" ]; then
        tsh_message "message" "manual tests copied: $counterHand"
      fi
      if ! [ "$counterDo" == "0" ]; then
        tsh_message "message" "generated tests: $counterDo"
      fi
    fi
    popd > /dev/null
    pushd "${problemDirectory}/tests" > /dev/null 2> /dev/null || tsh_message "error" "directory “tests” was not created by doall" "fatal"
    find_tests
    tests=(${result[*]})
    if [ "${#tests[*]}" == "0" ]; then
      tsh_message "error" "there are no tests" "non-fatal"
      popd > /dev/null
      continue
    fi
    tsh_message "message" "found tests: ${#tests[*]}"
    tsh_message -n "message" "converting tests"
    for testNumber in ${tests[*]}; do
      echo -n '.'
      case "$OPERATION_SYSTEM" in
        ('Linux')
          dos2unix "$testNumber" 2> /dev/null || tsh_message 'warning' "“dos2unix ${testNumber}” failed"
          if [ -e "$testNumber.a" ] ; then
            dos2unix "$testNumber.a" 2> /dev/null || tsh_message 'warning' "“dos2unix ${testNumber}.a” failed"
          fi ;;
        (*)
          unix2dos "$testNumber" 2> /dev/null || tsh_message 'warning' "“unix2dos ${testNumber}” failed"
          if [ -e "$testNumber.a" ] ; then
            unix2dos "$testNumber.a" 2> /dev/null || tsh_message 'warning' "“unix2dos ${testNumber}.a” failed"
          fi ;;
      esac
    done
    echo 'ok'
    validatorName=""
    validatorLanguage=""
    for i in '../source/validator' '../source/validate' '../src/validator' '../src/validate' 'validator' 'validate'; do
      if find_source "$i"; then
        validatorName="$i.$result"
        validatorLanguage="$(language "$result")"
        break;
      fi
    done
    if [ "$validatorName" == "" ]; then
      tsh_message "warning" "validator not found, tests wouldn't be validated"
    else
      validator="$(source_compile "$validatorName" "$validatorLanguage")"
      tsh_message -n "message" "validating tests"
      for testNumber in ${tests[*]}; do
        echo -n "."
        source_run "$validator" "$testNumber" || tsh_message "error" "test [$testNumber] failed validation"
      done
      echo "ok"
    fi
    if ! find_solution "../" "$pSolutionSuffix" "$problemName"; then
      tsh_message "warning" "solution not found, answers wouldn't be generated"
      popd > /dev/null
      continue
    fi
    solutionName="$result"
    solutionLanguage="`echo "$solutionName" | sed -e 's/^.*\.\([^.]*\)$/\1/'`"
    solution="$(source_compile "../$solutionName" "$(language "$solutionLanguage")")"
    tsh_message -n "message" "generate answers"
    for testNumber in ${tests[*]}; do
      if [ -f "$testNumber.a" ]; then
        echo -n "+"
        continue
      fi
      echo -n "."
      cp "$testNumber" "$pInputFileName"
      cp "$testNumber" "$pInputFileName"
      if [ "$pInputFile" == "<stdin>" ]; then
        inputFile="$pInputFileName";
      else
        inputFile=""
      fi
      if [ "$pOutputFile" == "<stdout>" ]; then
        outputFile="$pOutputFileName";
      else
        outputFile=""
      fi
      source_run "$solution" "$inputFile" "$outputFile" || tsh_message "error" "solution failed on test [$testNumber]"
      cp "$pOutputFileName" "$testNumber.a"
    done
    echo "ok"
    rm --force "$pInputFileName" "$pOutputFileName"
    do_check "$problemName" "$solution"
    popd > /dev/null
  done
}


clean_binary()
{
  for i in "$1"/*; do
    if [ -f "$i.cpp" ] || [ -f "$i.c++" ] || [ -f "$i.c" ] || [ -f "$i.dpr" ] || [ -f "$i.pas" ] || [ -f "$i.PAS" ]; then
      tsh_message "message" "removed: $i"
      rm --force "$i"
    fi
  done
}

t_check()
{
  find_problem "`pwd`"
  problems=(${result[*]});
  for (( currentProblem = 0; currentProblem < ${#problems[*]}; currentProblem++ )); do
    problemDirectory="${problems[$currentProblem]}"
    problemName="`echo "$problemDirectory" | sed -e 's/^.*[\/.]\([^\/]*\)$/\1/'`"
    tsh_message "message" "=== working with problem “$problemName” ==="
    readProblemProperties
    pushd "$problemDirectory/tests" > /dev/null
    solutionSuffix="${tParameters[1]}"
    if ! find_solution "../" "$solutionSuffix" "$problemName"; then
      tsh_message "warning" "solution not found: “$solutionSuffix”"
      popd > /dev/null
      continue
    fi
    solutionName="$result"
    solutionLanguage="`echo "$solutionName" | sed -e 's/^.*\.\([^.]*\)$/\1/'`"
    solution="$(source_compile "../$solutionName" "$(language "$solutionLanguage")")"
    find_tests
    tests=(${result[*]})
    do_check "$problemName" "$solution"
    popd > /dev/null
  done
}

t_clean()
{
  find_problem "`pwd`"
  problems=(${result[*]});
  for (( currentProblem = 0; currentProblem < ${#problems[*]}; currentProblem++ )); do
    problemDirectory="${problems[$currentProblem]}"
    pushd "$problemDirectory" > /dev/null
    if [ "$arg_NoRemoveTests" != 'true' ]; then
      rm --force tests/[0-9][0-9]{,[0-9]}{,.a}
    fi
    rm --force tests/tests.gen
    for i in '.' 'source' 'src' 'tests'; do
      if ! [ -d "$i" ]; then
        continue;
      fi
      rm --force "$i"/*.{in,out,log,exe,dcu,ppu,o,obj,class,hi,manifest,pyc,pyo}
      clean_binary "$i"
    done
    # try to invoke custom clear scripts
    for i in 'src' 'source' 'tests'; do
      if ! [ -d "$i" ]; then
        continue
      fi
      pushd "$i" > /dev/null
      [ -f wipe.py ] && (python wipe.py || tsh_message 'error' "wipe.py failed")
      popd > /dev/null
    done
    # remove tests directory sometimes
    if ( [ -d "src" ] || [ -d "source" ] ) && [ "$arg_NoRemoveTests" != 'true' ] && [ -d "tests" ] ; then
      rmdir "tests" || tsh_message "warning" "directory “tests” could not be cleaned up while directory “src” exists"
    fi
    popd > /dev/null
  done
}


t_help()
{
  case "${tParameters[1]}" in
    ('build') help_build;;
    ('clean') help_clean;;
    (*) help_common;;
  esac
}

t_usage()
{
  help_usage
}


# code ^_^

# parse command line
tParameters=()
for i in $*; do
  if [ "$i" == '--allow-wa' ]; then
    arg_AllowWA='true'
  elif [ "$i" == '--no-remove-tests' ] || [ "$i" == '-t' ]; then
    arg_NoRemoveTests='true'
  else
    tParameters[${#tParameters[*]}]="$i"
  fi
done
tCommand="${tParameters[0]}"

case "$tCommand" in
  ('build') t_build;;
  ('check') t_check;;
  ('clean') t_clean;;
  ('help') t_help;;
  ('') t_usage;;
  (*) echo "$scriptName: $tCommand: unknown command"
      echo "try “$scriptName help”" ;;
esac