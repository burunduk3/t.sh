
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
    ('c') suffix="$BINARY_SUFFIX" ;;
    ('cpp') suffix="$BINARY_SUFFIX" ;;
    ('c++') suffix="$BINARY_SUFFIX" ;;
    ('dpr') suffix="$BINARY_SUFFIX" ;;
    ('java') suffix=".class" ;;
    ('pas') suffix="$BINARY_SUFFIX" ;;
    ('pl') suffix=".pl" ;;
    ('py') suffix=".py" ;;
    ('sh') suffix=".sh" ;;
    (*) tsh_message "error" "unknown language (“$language”)";;
  esac
  if [ ${#*} -lt 3 ]; then
    targetFile="$(echo "$sourceFile" | sed -e 's/\.[^.]*$//')$suffix"
  else
    targetFile="$3"
  fi
  result="$targetFile"
  if [ ! "$sourceFile" -nt "$targetFile" ]; then
    tsh_message "message" "compile($sourceFile) skipped"
    return;
  fi
  case "$language" in
    ("c") compileCommand="gcc $CFLAGS -o $targetFile -x c $sourceFile" ;;
    ("cpp") compileCommand="g++ $CXXFLAGS -o $targetFile -x c++ $sourceFile" ;;
    ('c++') compileCommand="g++ $CXXFLAGS -o $targetFile -x c++ $sourceFile" ;;
    ("dpr") compileCommand="fpc $FPCFLAGS -o$targetFile $sourceFile" ;;
    ("java") compileCommand="javac $sourceFile" ;;
    ("pas") compileCommand="fpc $FPCFLAGS -o$targetFile $sourceFile" ;;
    ("pl") compileCommand="true" ;;
    ("py") compileCommand="true" ;;
    ("sh") compileCommand="true" ;;
    (*) tsh_message "error" "unknown language (“$language”)";;
  esac
  tsh_message "message" "$compileCommand"
  $compileCommand || tsh_message "error" "compile failed"
}

# source_run — function for running program using one of standart schemes
#   usage: solution_run <binary-file> <scheme> [<input-file> [<output-file>]]
#   currently there are 2 schemes that differs from others: java and perl
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
    'c++') runCommand="./$binaryFile ${*:5}" ;;
    "cpp") runCommand="./$binaryFile ${*:5}" ;;
    "dpr") runCommand="./$binaryFile ${*:5}" ;;
    "java")
      classPath=`echo "./$binaryFile" | sed -e "s/\/[^\/]*$//"`
      className=`echo "./$binaryFile" | sed -e "s/^.*\/\([^\/]*\)\.class$/\1/"`
      if [ "$classPath" == "" ]; then
        classPath="."
      fi
      runCommand="java $JAVAFLAGS -cp $classPath $className ${*:5}"
    ;;
    "pas") runCommand="./$binaryFile ${*:5}" ;;
    "pl") runCommand="perl $binaryFile ${*:5}" ;;
    #"py") runCommand="python $binaryFile ${*:5}" ;;
    "py") runCommand="./$binaryFile ${*:5}" ;;
    "sh") runCommand="bash $binaryFile ${*:5}" ;;
    *) tsh_message "error" "unknown language (“$language”)" ;;
  esac
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
}

