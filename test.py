#!/usr/bin/

class Test:
    def __init__ ( self, path ):
        self.__path = path
        self.__answer = None

    path = property (lambda self: self.__path)
    answer = property (lambda self: self.__answer)
    @answer.setter
    def answer ( self, value ):
        self.__answer = value


class Answer:
    def __init__ ( self, path, input ):
        self.__path = path
        self.__input = input

    path = property (lambda self: self.__path)


