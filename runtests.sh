#!/bin/bash

set -e

if [ -z "$VIRTUAL_ENV" ]; then
	if [ -e "../bin/activate" ]; then
		echo "Activating your environment for you"
		. ../bin/activate
	else 
		echo "Please activate your environment first!"
	fi
fi

if [ ! -x "/usr/bin/realpath" ]; then
	echo "You do not have realpath installed"
	echo "Please run apt-get install realpath"
	exit 1;
fi

realpath=$(realpath $0)
projectpath=$(dirname "$realpath")
bootstrappath="$projectpath/modules/bootstrap/files/usr/lib/hypernode/"

export PYTHONPATH="$PYTHONPATH:$bootstrappath"

if [ "$1" = "--jenkins" ]; then
	nosetests --with-xunit --with-xcoverage --cover-erase --cover-package=hypernode;
	./pep8.sh
else
	watch -n 0.1 -c -- "
		nosetests --with-yanc --yanc-color=on --with-xcoverage --cover-erase --cover-package=hypernode $*;
		./pep8.sh"
fi
