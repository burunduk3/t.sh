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

class RunResult:
    class RUNTIME:
        pass
    class LIMIT_TIME:
        pass
    class LIMIT_IDLE:
        pass
    class LIMIT_MEMORY:
        pass
    class OK:
        pass

    def __init__ ( self, result, exitcode, comment=None, *, peak_time, peak_memory, outputs=(b'', b'') ):
        self.__result = result
        self.__exitcode = exitcode
        self.__comment = comment
        self.__peak_time = peak_time
        self.__peak_memory = peak_memory
        self.__stdout, self.__stderr = map (lambda x: x.decode ('utf8') if x is not None else None, outputs)

    value = property (lambda self: self.__result)
    exitcode = property (lambda self: self.__exitcode)
    stdout = property (lambda self: self.__stdout)
    stderr = property (lambda self: self.__stderr)
    time = property (lambda self: self.__peak_time)
    memory = property (lambda self: self.__peak_memory)

    def __bool__ ( self ):
        return self.__result is RunResult.OK

    def __str__ ( self ):
        if self.__result is RunResult.OK:
            if self.__comment is not None:
                return "[ok] " + self.__comment
            else:
                return "[ok]"
        if self.__result is RunResult.RUNTIME:
            return "exit code: %d" % self.__exitcode
        if self.__result is RunResult.LIMIT_TIME:
            return "time limit exceeded"
        if self.__result is RunResult.LIMIT_IDLE:
            return "idleness limit exceeded"
        if self.__result is RunResult.LIMIT_MEMORY:
            return "memory limit exceeded"
        raise NotImplementedError ("%s.__str__, result=%s" % (type (self), self.__result))
#         if r.result == RunResult.RUNTIME:
#             raise Error ('Runtime error (%s).' % r.comment)
#         elif r.result == RunResult.LIMIT_TIME:
#             raise Error ('Time limit exceeded (%s).' % r.comment)
#         elif r.result == RunResult.LIMIT_MEMORY:
#             raise Error ('Memory limit exceeded (%s)' % r.comment)
#         elif r.result == RunResult.OK:
#         else:
#             raise Error ('Invokation failed (%s).' % r.comment)

    @classmethod
    def ok ( cls, **kwargs ):
        return cls (RunResult.OK, 0, **kwargs)

    @classmethod
    def exitCode ( cls, code, **kwargs ):
        if code == 0:
            return cls (RunResult.OK, 0, **kwargs)
        else:
            return cls (RunResult.RUNTIME, code, **kwargs)

    @classmethod
    def runtime ( cls, code, comment, **kwargs ):
        return cls (RunResult.RUNTIME, code, comment, **kwargs)

    @classmethod
    def limitTime ( cls, comment, **kwargs ):
        return cls (RunResult.LIMIT_TIME, -1, comment, **kwargs)

    @classmethod
    def limitIdle ( cls, comment, **kwargs ):
        return cls (RunResult.LIMIT_IDLE, -1, comment, **kwargs)

    @classmethod
    def limitMemory ( cls, comment, **kwargs ):
        return cls (RunResult.LIMIT_MEMORY, -1, comment, **kwargs)

