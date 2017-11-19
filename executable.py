#!/usr/bin/env python3

from tlib import Module


class Executable (Module):
    def __init__ ( self, arguments, source, *args, path, **kwargs ):
        super (Executable, self).__init__ (*args, **kwargs)
        self.__arguments = arguments
        self.__source = source
        self.__path = path

    path = property (lambda self: self.__path)

    def __str__ ( self ):
        if self.__source is not None:
            return self.__source
        return ' '.join (self.__arguments)

    def run ( self, arguments=[], **kwargs ):
        if self.__source is not None and self.__source.directory is not None:
            kwargs['directory'] = self.__source.directory
        return self._run (self.__arguments + arguments, **kwargs)


