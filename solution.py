#!/usr/bin/env python3

from settings import Settings
from source import Source

class Solution (Source):
    def __init__ ( self, *args, problem, defaults=None, **kwargs ):
        super (Solution, self).__init__ (*args, **kwargs)
        self.__problem = problem
        self.__settings = Settings (defaults if defaults is not None else problem.defaults)

    limit_time = property (lambda self: self.__settings.limit_time)
    limit_idle = property (lambda self: self.__settings.limit_idle)
    limit_memory = property (lambda self: self.__settings.limit_memory)
    filename_input = property (lambda self: self.__settings.filename_input)
    filename_output = property (lambda self: self.__settings.filename_output)

