
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

