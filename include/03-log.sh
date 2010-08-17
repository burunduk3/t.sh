
# echo_colored: outputs one-line colored message
#   usage: echo_colored <color> <message>
#   color should be in vt100 style (for example, “1;31” means bold red)
#   COLOR_* consants can be used
#   variable COLOR_DISABLE disables coloring when equals to “true”
function echo_colored() {
  if [ "$COLOR_DISABLE" == 'true' ]; then
    echo "${*:2}"
  else
    echo $'\e['"$1"'m'"${*:2}"$'\e[0m'
  fi
}
COLOR_RED="1;31"
COLOR_GREEN="1;32"
COLOR_YELLOW="1;33"
COLOR_WHITE="1;37"
COLOR_BLUE="1;34"
COLOR_PURPLE="1;35"
COLOR_CYAN="1;36"
COLOR_DISABLE='false'

# tsh_message: print message and exits if out to be so.
#   usage: tsh_message [-n] <message-type> <message> [<exit-flag>]
#     -n flag means no line break after output
#     exit flag should be “fatal” or “non-fatal”, “fatal” means exiting
#     default value of exit flag depends on error type, “fatal“ and “error” types exits
#     error type can be one of following values:
#       fatal — means that there was error and there is no way to continue t.sh
#       error — means error that can be ignored but behviour of t.sh is undefined since it
#       warning — means error that can be ignored in most cases, otherwise t.sh will generate stronger error later
#       notice — means something
#       message — general output message
#       debug — means information that was used for debugging. This should not appear in final version of t.sh
#     theese types are displayed with different colors ^_~
typeset -A MESSAGE_COLOR
MESSAGE_COLOR['fatal']="$COLOR_RED"
MESSAGE_COLOR['error']="$COLOR_RED"
MESSAGE_COLOR['warning']="$COLOR_YELLOW"
MESSAGE_COLOR['notice']="$COLOR_GREEN"
MESSAGE_COLOR['message']="$COLOR_CYAN"
MESSAGE_COLOR['debug']="$COLOR_WHITE"
function tsh_message()
{
  lineBreak="true"
  if [ "$1" == "-n" ]; then
    lineBreak="false"
    shift
  fi
  errorType="$1"
  text="$(echo_colored "${MESSAGE_COLOR[$1]}" "[$scriptName, $errorType]" "$2")"
  if [ "$lineBreak" == 'false' ]; then
    echo -n "$text"
  else
    echo "$text"
  fi
  if [ "$1" == 'warning' ] || [ "$1" == 'notice' ] || [ "$1" == 'message' ] || [ "$1" == 'debug' ]; then
    exitFlag='non-fatal'
  else
    exitFlag='fatal'
  fi
  if [ ${#*} == 3 ]; then
    exitFlag="$3"
  fi
  case "$exitFlag" in
    ('fatal') exit 239;;
    ('non-fatal') return;;
    (*) echo_colored $COLOR_RED "[$scriptName, internal error]" "incorrect exit flag “$exitFlag”";;
  esac
}

