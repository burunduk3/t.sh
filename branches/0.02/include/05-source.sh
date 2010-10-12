
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

