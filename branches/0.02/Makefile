.PHONY: all

all: binary/t.sh

binary/t.sh: t.sh.main include/01-basic.sh include/02-help.sh include/03-log.sh include/04-find.sh include/05-source.sh\
             include/06-check.sh include/07-properties.sh include/08-build.sh include/09-clean.sh include/10-main.sh
	echo 'merge t.sh'
	cat $^ > "$@"
	chmod a+x "$@"

