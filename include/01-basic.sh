
scriptName=`basename $0`
INCLUDE_PATH="../../../include"

OPERATION_SYSTEM=`uname || echo 'system_error'` # Windows is system error ^_~

# GCC flags
gccVersionString=`gcc --version | head -n 1`
gccVersion=${gccVersionString##* }
gccVersionMajor=${gccVersion##*.}
if [ $gccVersionMajor == "4" ] ; then
  CFLAGS="-O2 -Wall -Wextra -I $INCLUDE_PATH -D__T_SH__"
else
  CFLAGS="-O2 -Wall -I $INCLUDE_PATH -D__T_SH__"
fi
CXXFLAGS="${CFLAGS}"
# End of GCC flags

FPCFLAGS="-O3 -FE. -v0ewn -Sd -Fu$INCLUDE_PATH -Fi$INCLUDE_PATH -d__T_SH__"
JAVAFLAGS="-Xmx256M -Xss128M"
BINARY_SUFFIX=""
if [ "$OPERATION_SYSTEM" != "Linux" ]; then
  CFLAGS="$CFLAGS -Wl,--stack=134217728"
  CXXFLAGS="$CXXFLAGS -Wl,--stack=134217728"
  BINARY_SUFFIX=".exe"
fi

