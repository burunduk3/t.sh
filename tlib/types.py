import base64
import re
import struct

from .datalog import Type

class String (Type):
    def __init__ ( self, value ):
        self.__value = str (value)

    value = property (lambda self: self.__value)

    def __str__ ( self ):
        return self.__value

    def dump ( self ):
        if re.match ("^[0-9a-zA-Zа-яА-Я\\._+-]+$", self.__value):
            yield self.__value
        else:
            yield '"' + \
                self.__value. \
                replace ('\\', '\\\\').replace ('\n', '\\n').replace ('\t', '\\t'). \
                replace ('\0', '\\0').replace ('\r', '\\r').replace ('"', '\\"') + \
                '"'

    def __eq__ ( self, x ):
        return self.__value == x.__value

    # @classmethod
    # def dump ( cls, value ):
    #     return cls (value).dump ()

    @classmethod
    def parse ( cls, data ):
        return cls (next (data))


class Float (Type):
    def __init__ ( self, value ):
        self.__value = float (value)

    value = property (lambda self: self.__value)

    def __str__ ( self ):
        return '%.20f' % self.__value

    def dump ( self ):
        yield base64.b16encode (struct.pack ('d', self.__value)).decode ('ascii')

    def __eq__ ( self, x ):
        return self.__value == x.__value

    @classmethod
    def parse ( cls, data ):
        value = next (data)
        if re.match ('^[0-9a-f]{16}$', value):
            value = struct.unpack ('d', base64.b16decode (value))[0]
        return cls (value)


class Integer (Type):
    def __init__ ( self, value ):
        self.__value = int (value)

    value = property (lambda self: self.__value)

    def __str__ ( self ):
        return '%d' % self.__value

    def dump ( self ):
        yield str (self.__value)

    def __eq__ ( self, x ):
        return self.__value == x.__value

    @classmethod
    def parse ( cls, data ):
        return cls (next (data))


