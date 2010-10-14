
# utilitary

tsh_util_dos2unix()
{
  if dos2unix "$1" 2> /dev/null ; then
    return 0
  fi
  if dos2unix "$1" "$1.tmp-dos2unix" && mv "$1.tmp-dos2unix" "$1" ; then
    return 0
  fi
  return 1
}

tsh_util_unix2dos()
{
  if unix2dos "$1" 2> /dev/null ; then
    return 0
  fi
  if unix2dos "$1" "$1.tmp-unix2dos" && mv "$1.tmp-unix2dos" "$1" ; then
    return 0
  fi
  return 1
}

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
      source_compile "doall.$doSuffix" "$doSuffix"
      doBinary="$result"
      source_run "$doBinary" "$doSuffix" "" ""  || tsh_message "error" "doall.sh failed"
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
          source_compile "do$j.$doSuffix" "$doSuffix"
          doBinary="$result"
          source_run "$doBinary" "$doSuffix" "" "$testsDirectory/$j"
        elif find_source "gen$j"; then
          counterDo=$(($counterDo + 1))
          doSuffix="$result"
          source_compile "gen$j.$doSuffix" "$doSuffix"
          doBinary="$result"
          source_run "$doBinary" "$doSuffix" "" "$testsDirectory/$j"
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
          tsh_util_dos2unix "$testNumber" || tsh_message 'warning' "“dos2unix ${testNumber}” failed"
          if [ -e "$testNumber.a" ] ; then
            tsh_util_dos2unix "$testNumber.a" || tsh_message 'warning' "“dos2unix ${testNumber}.a” failed"
          fi ;;
        (*)
          tsh_util_unix2dos "$testNumber" || tsh_message 'warning' "“unix2dos ${testNumber}” failed"
          if [ -e "$testNumber.a" ] ; then
            tsh_util_unix2dos "$testNumber.a" || tsh_message 'warning' "“unix2dos ${testNumber}.a” failed"
          fi ;;
      esac
    done
    echo 'ok'
    validatorName=""
    validatorLanguage=""
#    validatorBinary=""
    for i in '../source/validator' '../source/validate' '../src/validator' '../src/validate' 'validator' 'validate'; do
      if find_source "$i"; then
        validatorName="$i.$result"
        validatorLanguage="$result"
#        validatorBinary="$i"
        break;
      fi
    done
    if [ "$validatorName" == "" ]; then
      tsh_message "warning" "validator not found, tests wouldn't be validated"
    else
      source_compile "$validatorName" "$validatorLanguage"
      # "$validatorBinary"
      validatorBinary="$result"
      tsh_message -n "message" "validating tests"
      for testNumber in ${tests[*]}; do
        echo -n "."
        source_run "$validatorBinary" "$validatorLanguage" "$testNumber" || tsh_message "error" "test [$testNumber] failed validation"
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
    source_compile "../$solutionName" "$solutionLanguage"
    solutionBinary="$result"
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
      source_run "$solutionBinary" "$solutionLanguage" "$inputFile" "$outputFile" || tsh_message "error" "solution failed on test [$testNumber]"
      cp "$pOutputFileName" "$testNumber.a"
    done
    echo "ok"
    rm --force "$pInputFileName" "$pOutputFileName"
    do_check "$problemName" "$solutionBinary" "$solutionLanguage"
    popd > /dev/null
  done
}

