import os.path

import common as t

def detector_python( source ):
    with open (source, 'r') as f:
        shebang = f.readline ()
        if shebang[0:2] != '#!':
            shebang = ''
        if 'python3' in shebang:
            return 'python3'
        elif 'python2' in shebang:
            return 'python2'
        else:
            # python3 is default
            return 'python3'

suffixes = {
    'c': 'c', 'c++': 'c++', 'C': 'c++', 'cxx': 'c++', 'cpp': 'c++',
    'pas': 'pascal', 'dpr': 'delphi',
    'java': 'java', 'pl': 'perl', 'py': detector_python, 'sh': 'bash'
}

def compiler_detect ( path ):
    suffix = path.split ('.')[-1]
    detector = suffixes[suffix]
    if isinstance (detector, str):
        return detector
    return detector (path)

def set_compilers ( value ):
    global compilers
    compilers = value

class Source:
    def __init__ ( self, path, compiler=None ):
        self.__path = path
        self.__compiler = compiler # TODO: detect if None
        if self.__compiler is None:
            self.__compiler = compiler_detect (self.__path)
        self.__executable = None

    def __str__ ( self ):
        return self.__path
    def __eq__ ( self, other ):
        return type (other) is Source and self.__path == other.__path and self.__compiler == other.__compiler

    def compile ( self ):
        global compilers
        compiler = compilers[self.__compiler]
        self.__executable = compiler (self.__path)
        if self.__executable is None:
           raise t.Error ("%s: compilation error" % self.__path)
    def run ( self, *arguments, **kwargs ):
        if self.__executable is None:
            self.compile ()
        return self.__executable (arguments, **kwargs)
    
    path = property (lambda self: self.__path)
    compiler = property (lambda self: self.__compiler)
    executable = property (lambda self: self.__executable)

    @classmethod
    def find ( cls, path ):
        for filename in [path + '.' + suffix for suffix in suffixes.keys ()]:
            if os.path.isfile(filename):
                return cls (filename)
        if os.path.isfile(path):
            return cls (path)
        return None


