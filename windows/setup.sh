#!/bin/bash

pushd ../ > /dev/null 2>&1
directory=$(pwd)
if ! [ -f "$directory/t.sh" ]; then
  echo "error: t.sh not found in $directory"
  exit 1;
fi
echo " * t.sh directory: $directory"
echo " * creating t.sh.cmd file to allow invoke t.sh from anywhere just typing 't.sh'"
popd > /dev/null
(
    echo "@echo off"
    echo ""
    echo "bash \"$directory/t.sh\" %*"
    echo ""
) > 't.sh.cmd'
echo " * don't forget to add this directory to your PATH enviropment variable"
echo " * $(pwd)"

