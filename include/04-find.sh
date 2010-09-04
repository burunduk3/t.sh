
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

