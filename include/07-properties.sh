
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

