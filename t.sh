#!/bin/bash

# t.sh test tool — clone of outdated t.cmd
# version 0.01-r1
# copyright (c) Oleg Davydov, Yury Petrov
# This program is free sortware, under GPL, for great justice...

# questions
#   1. If there is directory “tests”, shall we recursive scan into subdirectories?
#   2. If there is directory “src”, should “clean” command remove “tests” directory?

# todo
#   1. Parameters for running java and compiling all
#   2. [echo_colored] support for -n [done]
#   3. Advanced coloring
#   4. Standard input/output (option?)
#   5. Replace printf "%02d" $i (ex-seq...) with something even more appropriate.

# changelog
#   1. 2009-11-06: src directory support
#   2. 39-312 (2009-11-09): perl support, doall-generated answers support
#   3. 2009-11-17: seq -> printf
#   4. 2009-11-20: -D__T_SH__
#   5. 40-034 (20010-02-04): added compile skipping (like make)

scriptName="$0"
#INCLUDE_PATH="`echo $0 | sed -e 's/\/.*$//'`/../../include"
INCLUDE_PATH="../../../include"

OPERATION_SYSTEM=`uname || echo 'system_error'` # Windows is system error ^_~

CFLAGS="-O2 -Wall -I $INCLUDE_PATH -D__T_SH__"
CXXFLAGS="-O2 -Wall -I $INCLUDE_PATH -D__T_SH__"
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
  echo "  either “src” or “tests” subdirectory."
  echo "  For each problem directory found, the following procedure is executed:"
  echo "  If the “src” directory exists, t.sh uses it as source for tests,"
  echo "  otherwise it users the “tests” directory itself."
  echo "  Note: <test> stands for any (or every) string of 2–3 digits."
  echo "  Step 0: generate tests"
  echo "    t.sh searches the source directory for doall.sh, then for doall.cmd or doall.bat."

  echo "    If none of above has been found, t.sh tries to generate each test separately,"
  echo "    using “do<test>.*” files or just copying “<test>.hand” or “<test>.manual” files."
  echo "  Step 1: validate tests"
  echo "    TODO: validate process"
  echo "    If no validator was found, the step is skipped with a warning"
  echo "  Step 2: generate answers"
  echo "    If exact solution was specified, it is used. Otherwise, file t.sh greps the"
  echo "    “problem.properties” file for a string “solution” and tries to use it."
  echo "    Then t.sh runs the solution on every test and copies resulting files to “<test>.a”"
  echo "  Step 3: check"
  echo "    If some checker is present (a program named “check”, “checker”, “check_<problem>”),"
  echo "    the model solution is run on every test and checked using that checker."
}

function help_common()
{
  echo "TODO: help common"
}

function help_usage()
{
  echo "TODO: usage!"
}


# === commmon functions ===

# echo_colored: outputs one-line colored message
#   usage: echo_colored <color> <message>
#   color should be in vt100 style (for example, “1;31” means red)
#   COLOR_* consants can be used
#   variable COLOR_DISABLE disables coloring when equals to “1”
#   variable lineBreak disables line break after output when equals to “false”
function echo_colored()
{
  if [ "$COLOR_DISABLE" == "1" ]; then
    if [ "$lineBreak" == "false" ]; then
      echo -n "$1"
    else
      echo "$1"
    fi
  else
    if [ "$lineBreak" == "false" ]; then
      printf "\e[%sm%s\e[0m" "$1" "${*:2}"
    else
      printf "\e[%sm%s\e[0m\n" "$1" "${*:2}"
    fi
  fi
}
COLOR_RED="1;31"
COLOR_GREEN="1;32"
COLOR_YELLOW="1;33"
COLOR_WHITE="1;37"
COLOR_BLUE="1;34"
COLOR_PURPLE="1;35"
COLOR_CYAN="1;36"
COLOR_DISABLE="0"

# tsh_information: print message and exits if out to be so.
#   usage: tsh_information [-n] <error-type> <error-message> [<exit-flag>]
#     -n flag means no line break after output
#     exit flag should be “fatal” or “non-fatal”, “fatal” means exiting
#     default value of exit flag depends on error type, “fatal“ and “error” types exits
#     error type can be one of following values:
#       fatal — means that there was error and there is no way to continue t.sh
#       error — means error that can be ignored but behviour of t.sh is undefined since it
#       warning — means error that can be ignored in most cases, otherwise t.sh will generate stronger error later
#       notice — means something
#       information — means something about t.sh work
#       debug — means information that was used for debugging. This should not appear in final version of t.sh
#     theese types are displayed with different colors ^_~
function tsh_information()
{
  lineBreak="true"
  if [ "$1" == "-n" ]; then
    lineBreak="false"
    shift
  fi
  errorType="$1"
  case "$errorType" in
    "fatal")
      echo_colored $COLOR_RED "[$scriptName, $errorType]" "$2"
      exitFlag="fatal"
    ;;
    "error")
      echo_colored $COLOR_RED "[$scriptName, $errorType]" "$2"
      exitFlag="fatal"
    ;;
    "warning")
      echo_colored $COLOR_YELLOW "[$scriptName, $errorType]" "$2"
      exitFlag="non-fatal"
    ;;
    "notice")
      echo_colored $COLOR_GREEN "[$scriptName, $errorType]" "$2"
      exitFlag="non-fatal"
    ;;
    "information")
      echo_colored $COLOR_CYAN "[$scriptName, $errorType]" "$2"
      exitFlag="non-fatal"
    ;;
    "debug")
      echo_colored $COLOR_WHITE "[$scriptName, $errorType]" "$2"
      exitFlag="non-fatal"
    ;;
    *)
      echo_colored $COLOR_RED "[$scriptName, internal error]" "unknown error type, below error is shown"
      echo_colored $COLOR_RED "[$scriptName, $errorType]" "$2"
      exitFlag="non-fatal"
    ;;
  esac
  if [ ${#*} == 3 ]; then
    exitFlag="$3"
  fi
  case "$exitFlag" in
    "fatal") exit 239;;
    "non-fatal") return;;
    *) echo_colored $COLOR_RED "[$scriptName, internal error]" "incorrect exit flag “$exitFlag”";;
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
  if [ -d "$1/src" ]; then
    result[${#result[*]}]="$1"
  elif [ -d "$1/source" ]; then
    result[${#result[*]}]="$1"
  elif [ -d "$1/tests" ]; then
    result[${#result[*]}]="$1"
  fi
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
    tsh_information "error" "[recursive_problem] directory “$directory” doesn't looks like directory"
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
  for test_source_i in c cpp dpr java pas pl; do
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


# === source functions ===

# source_compile — function for compiling using one of standart schemes
#   usage: source_compile <sourceFile> <language> [<targetFile>]
#   see help compile for details
#   beware that java doesn't support changing target file name
#   in global valiable “result” returns real target name
function source_compile()
{
  sourceFile="$1"
  language="$2"
  case "$language" in
    "c") suffix="$BINARY_SUFFIX" ;;
    "cpp") suffix="$BINARY_SUFFIX" ;;
    "dpr") suffix="$BINARY_SUFFIX" ;;
    "java") suffix=".class" ;;
    "pas") suffix="$BINARY_SUFFIX" ;;
    "pl") suffix=".pl" ;;
    *) tsh_information "error" "unknown language (“$language”)";;
  esac
  if [ ${#*} -lt 3 ]; then
    targetFile="`echo "$sourceFile" | sed -e 's/\.[^.]*$//'`$suffix"
  else
    targetFile="$3"
  fi
  result="$targetFile"
  if [ ! "$sourceFile" -nt "$targetFile" ]; then
    tsh_information "information" "compile($sourceFile) skipped"
    return;
  fi
  case "$language" in
    "c") compileCommand="gcc $CFLAGS -o $targetFile -x c $sourceFile" ;;
    "cpp") compileCommand="g++ $CXXFLAGS -o $targetFile -x c++ $sourceFile" ;;
    "dpr") compileCommand="fpc $FPCFLAGS -o$targetFile $sourceFile" ;;
    "java") compileCommand="javac $sourceFile" ;;
    "pas") compileCommand="fpc $FPCFLAGS -o$targetFile $sourceFile" ;;
    "pl") compileCommand="true" ;;
    *) tsh_information "error" "unknown language (“$language”)";;
  esac
  tsh_information "information" "$compileCommand"
  $compileCommand || tsh_information "error" "compile failed"
}

# source_run — function for running program using one of standart schemes
#   usage: solution_run <binary-file> <scheme> [<output-file>]
#   currently there is 1 scheme that differs from others: java
#   if <output-file> is set, standart output of program is redirected to it
# TODO: better input/output redirect handling
function source_run()
{
  binaryFile="$1"
  language="$2"
  inputFile="$3"
  outputFile="$4"
  case "$language" in
    "c") runCommand="./$binaryFile ${*:5}" ;;
    "cpp") runCommand="./$binaryFile ${*:5}" ;;
    "dpr") runCommand="./$binaryFile ${*:5}" ;;
    "java")
      classPath=`echo "$binaryFile" | sed -e "s/\/[^\/]*$//"`
      className=`echo "$binaryFile" | sed -e "s/^.*\/\([^\/]*\)\.class$/\1/"`
      if [ "$classPath" == "" ]; then
        classPath="."
      fi
      runCommand="java $JAVAFLAGS -cp $classPath $className ${*:5}"
    ;;
    "pas") runCommand="./$binaryFile ${*:5}" ;;
    "pl") runCommand="perl $binaryFile ${*:5}" ;;
    *) tsh_information "error" "unknown language (“$language”)" ;;
  esac
#  if [ "$inputFile" != "" ]; then
#    runCommand="$runCommand < $inputFile"
#  fi
#  if [ "$outputFile" != "" ]; then
#    runCommand="$runCommand > $outputFile"
#  fi
  if [ "$inputFile" == "" ]; then
    if [ "$outputFile" == "" ]; then
      $runCommand || return 1
    else
      $runCommand > "$outputFile" || return 1
    fi
  else
    if [ "$outputFile" == "" ]; then
      $runCommand < "$inputFile" || return 1
    else
      $runCommand < "$inputFile" > "$outputFile" || return 1
    fi
  fi
#  $runCommand || return 1
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
  solutionBinary="$2"
  solutionLanguage="$3"
  checkerName=""
  for checkName in "../check" "../checker" "../checker_$problemName"; do
    if find_source "$checkName"; then
      checkerName="$checkName.$result"
      checkerLanguage="$result"
      break
    fi
  done
  if [ "$checkerName" == "" ]; then
    tsh_information "warning" "checker not found, solution wouldn't be checked"
    return 1
  fi
  source_compile "$checkerName" "$checkerLanguage"
  checkerBinary="$result"
  tsh_information "information" "checking solution"
  for testNumber in ${tests[*]}; do
    tsh_information -n "information" "test [$testNumber] "
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
    source_run "$solutionBinary" "$solutionLanguage" "$inputFile" "$outputFile" || tsh_information "error" "solution failed on test [$testNumber]"
    source_run "$checkerBinary" "$checkerLanguage" "" "" "$testNumber" "$pOutputFileName" "$testNumber.a" || tsh_information "error" "check failed on test [$testNumber]"
  done
  rm --force "$problemName."{in,out}
}

# ...

function readProblemProperties()
{
  if [ -f "$problemDirectory/problem.properties" ]; then
    pSolution=`cat "$problemDirectory/problem.properties" | grep "solution" | sed -e 's/^solution *= *//'`
    pInputFile=`cat "$problemDirectory/problem.properties" | grep "input-file" | sed -e 's/^input-file *= *//'`
    pOutputFile=`cat "$problemDirectory/problem.properties" | grep "output-file" | sed -e 's/^output-file *= *//'`
  fi
  if [ "$pInputFile" == "" ] || [ "$pInputFile" == "<stdin>" ]; then
    pInputFileName="$problemName.in"
  else
    pInputFileName="$pInputFile";
  fi
  if [ "$pOutputFile" == "" ] || [ "$pOutputFile" == "<stdout>" ]; then
    pOutputFileName="$problemName.out"
  else
    pOutputFileName="$pOutputFile";
  fi
}

# t.sh commands

t_build()
{
  find_problem "`pwd`"
  problems=(${result[*]});
  for (( currentProblem = 0; currentProblem < ${#problems[*]}; currentProblem++ )); do
    problemDirectory="${problems[$currentProblem]}"
    problemName="`echo "$problemDirectory" | sed -e 's/^.*[\/.]\([^\/]*\)$/\1/'`"
    tsh_information "information" "=== working with problem “$problemName” ==="
    readProblemProperties
    pSolutionSuffix=""
    if [ "$pSolution" != "" ]; then
      pSolutionSuffix="$pSolution"
    fi
    if [ "$1" != "" ]; then
      pSolutionSuffix="$1"
    fi

    if [ -d "${problemDirectory}/src" ] ; then
      pushd "${problemDirectory}/src" > /dev/null
    elif [ -d "${problemDirectory}/source" ] ; then
      pushd "${problemDirectory}/source" > /dev/null
    else
      pushd "${problemDirectory}/tests" > /dev/null
    fi
    # clean:
    rm --force [0-9][0-9]{,[0-9]}{,.a} || tsh_information "fatal" "rm failed"
    rm --force ../tests/[0-9][0-9]{,[0-9]}{,.a} || tsh_information "fatal" "rm failed"
    if [ -f "doall.sh" ]; then
      tsh_information "information" "run doall.sh"
      "./doall.sh" || tsh_information "error" "doall.sh failed"
    elif [ -f "doall.py" ]; then
      tsh_information "information" "run doall.py"
      python "doall.py" || tsh_information "error" "doall.py failed"
    elif [ -f doall.bat ] || [ -f doall.cmd ]; then
      if [ -f doall.cmd ]; then
        doallName="doall.cmd"
      else
        doallName="doall.bat"
      
      fi
      tsh_information "error" "found “$doallName” instead of “doall.sh”" "non-fatal"
      tsh_information "error" "  this might work under outdated OS like Windows" "non-fatal"
      tsh_information "error" "  but please add sh version of doall for compatibility" "non-fatal"
      cmd.exe "$doallName" || tsh_information "fatal" "cannot run “$doallName”"
    else
      counterHand="0";
      counterDo="0";
#      for j in `seq -w 00 99`; do
# This is still not enough good, replaced for compatibility.
      for (( i = 0; i < 100; i++ )) ; do
        j=`printf "%02d" $i`
        if [ -f "$j.hand" ]; then
          counterHand=$(($counterHand + 1))
          cp "$j.hand" "$j"
        elif [ -f "$j.manual" ]; then
          counterHand=$(($counterHand + 1))
          cp "$j.manual" "$j"
        else
          find_source "do$j" || continue
          doSuffix="$result"
          counterDo=$(($counterDo + 1))
          source_compile "do$j$doSuffix" "$doSuffix"
          doBinary="$result"
          source_run "$doBinary" "$doSuffix" "" "$j"
        fi
      done
      if ! [ "$counterHand" == "0" ]; then
        tsh_information "information" "manual tests copied: $counterHand"
      fi
      if ! [ "$counterDo" == "0" ]; then
        tsh_information "information" "generated tests: $counterDo"
      fi
    fi
    popd > /dev/null
    pushd "${problemDirectory}/tests" > /dev/null 2> /dev/null || tsh_information "error" "directory “tests” was not created by doall" "fatal"
    find_tests
    tests=(${result[*]})
    if [ "${#tests[*]}" == "0" ]; then
      tsh_information "error" "there are no tests" "non-fatal"
      popd > /dev/null
      continue
    fi
    tsh_information "information" "found tests: ${#tests[*]}"
    validatorName=""
    validatorLanguage=""
    validatorBinary=""
    if find_source "validator"; then # TODO: list of parameters for find_source
      validatorName="validator.$result"
      validatorLanguage="$result"
      validatorBinary="validator"
    elif find_source "validate"; then
      validatorName="validate.$result"
      validatorLanguage="$result"
      validatorBinary="validate"
    elif find_source "../src/validator"; then
      validatorName="../src/validator.$result"
      validatorLanguage="$result"
      validatorBinary="../src/validator"
    elif find_source "../src/validate"; then
      validatorName="../src/validate.$result"
      validatorLanguage="$result"
      validatorBinary="../src/validate"
    else
      tsh_information "warning" "validator not found, tests wouldn't be validated"
    fi
    if [ "$validatorLanguage" != "" ]; then
      source_compile "$validatorName" "$validatorLanguage" "$validatorBinary"
      validatorBinary="$result"
      tsh_information -n "information" "validating tests"
      for testNumber in ${tests[*]}; do
        echo -n "."
        source_run "$validatorBinary" "$validatorLanguage" "$testNumber" || tsh_information "error" "test [$testNumber] failed validation"
      done
      echo "ok"
    fi
    if ! find_solution "../" "$pSolutionSuffix" "$problemName"; then
      tsh_information "warning" "solution not found, answers wouldn't be generated"
      popd > /dev/null
      continue
    fi
    solutionName="$result"
    solutionLanguage="`echo "$solutionName" | sed -e 's/^.*\.\([^.]*\)$/\1/'`"
    source_compile "../$solutionName" "$solutionLanguage"
    solutionBinary="$result"
    tsh_information -n "information" "generate answers"
    for testNumber in ${tests[*]}; do
      if [ -f "$testNumber.a" ]; then
        echo -n "+"
        continue
      fi
      echo -n "."
      cp "$testNumber" "$problemName.in"
      if [ "$pOutputFile" == "<stdout>" ]; then
        source_run "$solutionBinary" "$solutionLanguage" "" "$pOutputFileName" || tsh_information "error" "solution failed on test [$testNumber]"
      else
        source_run "$solutionBinary" "$solutionLanguage" || tsh_information "error" "solution failed on test [$testNumber]"
      fi
      cp "$pOutputFileName" "$testNumber.a"
    done
    echo "ok"
    rm --force "$problemName."{in,out}
    do_check "$problemName" "$solutionBinary" "$solutionLanguage"
    popd > /dev/null
  done
}

clean_binary()
{
  for i in "$1"/*; do
    if [ -f "$i.cpp" ] || [ -f "$i.c" ] || [ -f "$i.dpr" ] || [ -f "$i.pas" ] || [ -f "$i.PAS" ]; then
      tsh_information "information" "removed: $i"
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
    tsh_information "information" "=== working with problem “$problemName” ==="
    readProblemProperties
    pushd "$problemDirectory/tests" > /dev/null
    solutionSuffix="$1"
    if ! find_solution "../" "$solutionSuffix" "$problemName"; then
      tsh_information "warning" "solution not found: “$solutionSuffix”"
      popd > /dev/null
      continue
    fi
    solutionName="$result"
    solutionLanguage="`echo "$solutionName" | sed -e 's/^.*\.\([^.]*\)$/\1/'`"
    source_compile "../$solutionName" "$solutionLanguage"
    solutionBinary="$result"
    find_tests
    tests=(${result[*]})
    do_check "$problemName" "$solutionBinary" "$solutionLanguage"
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
    rm --force *.{in,out,log,exe,dcu,ppu,o,obj,class,hi,manifest}
    rm --force tests/*.{in,out,log,exe,dcu,ppu,o,obj,class,hi,manifest}
    if [ "$1" != "--no-remove-tests" ]; then
      rm --force tests/[0-9][0-9]{,[0-9]}{,.a}
    fi
    rm --force tests/tests.gen
    clean_binary .
    if [ -d "src" ] ; then
      clean_binary "src"
    fi
    clean_binary "tests"
    if [ -d "src" ] ; then
      rmdir "tests" || tsh_information "warning" "directory “tests” could not be cleaned up while directory “src” exists"
    fi
    popd > /dev/null
  done
}

t_help()
{
  case "$1" in
    "build") help_build;;
    *) help_common;;
  esac
}

t_usage()
{
  help_usage
}


# code ^_^

tCommand="$1"

case "$tCommand" in
  "build") t_build ${*:2} ;;
  "check") t_check ${*:2} ;;
  "clean") t_clean ${*:2} ;;
  "help") t_help ${*:2} ;;
  "") t_usage ;;
  *) echo "$scriptName: $tCommand: unknown command"
     echo "try “$scriptName help”" ;;
esac
