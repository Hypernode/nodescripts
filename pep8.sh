#!/bin/bash
pep8 --ignore=E501,W292,W391 --repeat --exclude=migrations,build . | cut -c3- > pep8.log || /bin/true

count=$(wc -l pep8.log | cut -d ' ' -f 1)
filecount=$(cut -d ':' -f 1 pep8.log | sort | uniq | wc -l)

if [ "$count" = "0" ]; then
	echo "No PEP8 errors found"
else
	echo "Found $count errors in $filecount files"
	echo
fi
cat pep8.log
