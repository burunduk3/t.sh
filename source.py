#!/usr/bin/env python3

#
#    t.py: utility for contest problem development
#    Copyright (C) 2009-2017 Oleg Davydov
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#


from tlib import Module


class Source (Module):
    def __init__ ( self, path, compiler, *args, name=None, directory=None, **kwargs ):
        super (Source, self).__init__ (*args, **kwargs)
        self.__path = path
        self.__compiler = compiler
        self.__name = name
        self.__directory = directory
        self.__compiled = None

    path = property (lambda self: self.__path)
    directory = property (lambda self: self.__directory)
    executable = property (lambda self: self.__compiled)
    @executable.setter
    def executable ( self, value ):
        self.__compiled = value

    def __str__ ( self ):
        if self.__name is not None:
            return self.__name
        elif self.__directory is not None:
            return "%s in %s/" % (self.__path, self.__directory)
        else:
            return self.__path

    def compile ( self ):
        if self.__compiled is not None:
            return
        self.__compiled = self.__compiler (self, directory=self.__directory)

    def run ( self, *args, **kwargs ):
        self.compile ()
        return self.__compiled.run (*args, **kwargs)


