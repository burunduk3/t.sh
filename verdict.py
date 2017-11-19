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

from invoker.common import RunResult

class Verdict:
    def __init__ ( self, message, value, comment='', *, peak_time=None, peak_memory=None ):
        self.__message = message
        self.__value = value
        self.__comment = comment
        self.__peak_time = peak_time
        self.__peak_memory = peak_memory

    def __bool__ ( self ):
        return self.__value

    def __str__ ( self ):
        return self.__message

    comment = property (lambda self: self.__comment)
    peak_time = property (lambda self: self.__peak_time)
    peak_memory = property (lambda self: self.__peak_memory)

    @classmethod
    def ce ( cls ):
        return cls ("CE", False)

    @classmethod
    def fail_solution ( cls, test, result, **kwargs ):
        return cls ("%s/%d" % ({
            RunResult.RUNTIME: 'RE',
            RunResult.LIMIT_TIME: 'TL',
            RunResult.LIMIT_IDLE: 'IL',
            RunResult.LIMIT_MEMORY: 'ML',
        }[result.value], test), False, **kwargs)

    @classmethod
    def fail_checker ( cls, test, result, comment, **kwargs ):
        if result.value is RunResult.RUNTIME and result.exitcode == 1:
            return cls ("WA/%d" % test, False, comment, **kwargs)
        if result.value is RunResult.RUNTIME and result.exitcode == 2:
            return cls ("PE/%d" % test, False, comment, **kwargs)
        return cls ("JE/%d" % test, False, comment, **kwargs)

    @classmethod
    def ok ( cls, **kwargs ):
        return cls ("OK", True, **kwargs)

