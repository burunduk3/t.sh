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


