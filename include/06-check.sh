
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
    tsh_message "warning" "checker not found, solution wouldn't be checked"
    return 1
  fi
  source_compile "$checkerName" "$checkerLanguage"
  checkerBinary="$result"
  tsh_message "message" "checking solution"
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
    source_run "$solutionBinary" "$solutionLanguage" "$inputFile" "$outputFile" || tsh_message "error" "solution failed on test [$testNumber]"
    source_run "$checkerBinary" "$checkerLanguage" "" "" "$testNumber" "$pOutputFileName" "$testNumber.a" || tsh_message "$checkerError" "check failed on test [$testNumber]"
  done
  rm --force "$problemName."{in,out}
}

# ...

