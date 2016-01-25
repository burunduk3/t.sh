#
#    t.py: utility for contest problem development
#    Copyright (C) 2009-2016 Oleg Davydov
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
    RUNTIME, LIMIT_TIME, LIMIT_IDLE, LIMIT_MEMORY, OK = range (5)

    def __init__ ( self, result, exitcode, comment='' ):
        self.result, self.exitcode, self.comment = result, exitcode, comment

    @classmethod
    def ok ( cls ):
        return cls (RunResult.OK, 0)

    @classmethod
    def exitCode ( cls, code ):
        if code == 0:
            return cls (RunResult.OK, 0)
        else:
            return cls (RunResult.RUNTIME, code)

    @classmethod
    def runtime ( cls, code, comment ):
        return cls (RunResult.RUNTIME, code, comment)

    @classmethod
    def limitTime ( cls, comment ):
        return cls (RunResult.LIMIT_TIME, -1, comment)

    @classmethod
    def limitIdle ( cls, comment ):
        return cls (RunResult.LIMIT_IDLE, -1, comment)

    @classmethod
    def limitMemory ( cls, comment ):
        return cls (RunResult.LIMIT_MEMORY, -1, comment)

