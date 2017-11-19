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

class Constant (type):
    def __str__ (self):
        return self.__constant__

class Settings:
    class STDIN (metaclass=Constant):
        __constant__ = '<stdin>'
    class STDOUT (metaclass=Constant):
        __constant__ = '<stdout>'

    def __init__ (
        self, parent=None, *,
        limit_time=None, limit_idle=None, limit_memory=None,
        filename_input=None, filename_output=None
    ):
        self.__parent = parent
        self.__limit_time = limit_time
        self.__limit_idle = limit_idle
        self.__limit_memory = limit_memory
        self.__filename_input = filename_input
        self.__filename_output = filename_output
        if parent is None:
            assert self.__limit_time is not None
            assert self.__limit_idle is not None
            assert self.__limit_memory is not None
            assert self.__filename_input is not None
            assert self.__filename_output is not None

    @property
    def limit_time ( self ):
        if self.__limit_time is None:
            return self.__parent.limit_time
        return self.__limit_time

    @property
    def limit_idle ( self ):
        if self.__limit_idle is None:
            return self.__parent.limit_idle
        return self.__limit_idle

    @property
    def limit_memory ( self ):
        if self.__limit_memory is None:
            return self.__parent.limit_memory
        return self.__limit_memory

    @property
    def filename_input ( self ):
        if self.__filename_input is None:
            return self.__parent.filename_input
        return self.__filename_input

    @property
    def filename_output ( self ):
        if self.__filename_output is None:
            return self.__parent.filename_output
        return self.__filename_output


