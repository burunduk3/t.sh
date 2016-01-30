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

import sys


class Error ( Exception ):
    def __init__ ( self, comment ):
        super (Error, self).__init__ (comment)

    @classmethod
    def throw ( cls, *args ):
        raise cls (*args)

    @classmethod
    def ensure ( cls, expression, *args ):
        if not expression:
            raise cls (*args)


class Module:
    def __init__ ( self, t ):
        self._t = t

    _log = property (lambda self: self._t.log)
    _languages = property (lambda self: self._t.languages)


class Log:
    DEBUG, INFO, NOTICE, WARNING, ERROR, FATAL = range (6)

    def __init__( self ):
        self.__verbose = Log.INFO
        self.__color = {
            Log.DEBUG: 37, Log.INFO: 36, Log.NOTICE: 32,
            Log.WARNING: 33, Log.ERROR: 31, Log.FATAL: 31
        }
        self.__message = {
            Log.DEBUG: 'debug', Log.INFO: 'info', Log.NOTICE: 'notice',
            Log.WARNING: 'warning', Log.ERROR: 'error', Log.FATAL: 'fatal error'
        }

        self.debug = lambda text: self (text, Log.DEBUG)
        self.info = lambda text: self (text, Log.INFO)
        self.notice = lambda text: self (text, Log.NOTICE)
        self.warning = lambda text: self (text, Log.WARNING)
        self.error = lambda text: self (text, Log.ERROR)
        self.fatal = lambda text: self (text, Log.FATAL)

        self.__write = self.__write_default

    def verbose ( self, level=None ):
        if level is None:
            level = Log.DEBUG
        self.__verbose = level

    def __set_write ( self, write ):
        self.__write = write
    write = property (None, __set_write)

    def __call__( self, message, level=INFO, *, prefix=True, end='\n' ):
        if level < self.__verbose:
            return
        if prefix:
            message = "[t:%s] \x1b[1;%dm%s\x1b[0m%s" % \
                (self.__message[level], self.__color[level], message, end)
        else:
            message = message + end
        self.__write (message)

    @staticmethod
    def __write_default ( message ):
        sys.stdout.write (message)
        sys.stdout.flush ()

