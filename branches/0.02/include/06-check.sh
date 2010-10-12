
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

