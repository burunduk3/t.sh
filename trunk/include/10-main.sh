
t_help()
{
  case "${tParameters[1]}" in
    ('build') help_build;;
    ('clean') help_clean;;
    (*) help_common;;
  esac
}

t_usage()
{
  help_usage
}


# code ^_^

# parse command line
tParameters=()
for i in $*; do
  if [ "$i" == '--allow-wa' ]; then
    arg_AllowWA='true'
  elif [ "$i" == '--no-remove-tests' ] || [ "$i" == '-t' ]; then
    arg_NoRemoveTests='true'
  else
    tParameters[${#tParameters[*]}]="$i"
  fi
done
tCommand="${tParameters[0]}"

case "$tCommand" in
  ('build') t_build;;
  ('check') t_check;;
  ('clean') t_clean;;
  ('help') t_help;;
  ('') t_usage;;
  (*) echo "$scriptName: $tCommand: unknown command"
      echo "try “$scriptName help”" ;;
esac
