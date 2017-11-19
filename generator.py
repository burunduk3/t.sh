#!/usr/bin/env python3

from tlib import Module


class Generator (Module):
    def __init__ ( self, *args, problem, **kwargs ):
        super (Generator, self).__init__ (*args, **kwargs)
        self._problem = problem

    def run ( self ):
        raise NotImplementedError ("%s.run" % type (self))

    @classmethod
    def external ( cls, *args, **kwargs ):
        return ExternalGenerator (*args, **kwargs)


class ExternalGenerator (Generator):
    def __init__ ( self, source, *args, heuristics, directory_tests, **kwargs):
        super (ExternalGenerator, self).__init__ (*args, **kwargs)
        self.__source = source
        self.__heuristics = heuristics
        self.__directory_tests = directory_tests

    source = property (lambda self: self.__source)

    def __str__ ( self ):
        return str (self.__source)

    def run ( self ):
        result = self.__source.run ()
        if not result:
            raise self._error ("%s failed: %s" % (self.__source, result))
        return self.tests ()

    def tests ( self ):
        return self.__heuristics.tests_search (self.__directory_tests, self._problem)

