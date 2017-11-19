#!/usr/bin/env python3

import sys

class Color:
    class DEFAULT:
        pass
    class BLACK:
        pass
    class RED:
        pass
    class GREEN:
        pass
    class YELLOW:
        pass
    class BLUE:
        pass
    class MAGENTA:
        pass
    class CYAN:
        pass
    class WHITE:
        pass
    class BRIGHTBLACK:
        pass
    class BRIGHTRED:
        pass
    class BRIGHTGREEN:
        pass
    class BRIGHTYELLOW:
        pass
    class BRIGHTBLUE:
        pass
    class BRIGHTMAGENTA:
        pass
    class BRIGHTCYAN:
        pass
    class BRIGHTWHITE:
        pass


class VT100:
    def __init__ ( self ):
        self.__convert = {
            Color.DEFAULT: '\x1b[0m',
            Color.BLACK: '\x1b[30m',
            Color.RED: '\x1b[31m',
            Color.GREEN: '\x1b[32m',
            Color.YELLOW: '\x1b[33m',
            Color.BLUE: '\x1b[34m',
            Color.MAGENTA: '\x1b[35m',
            Color.CYAN: '\x1b[36m',
            Color.WHITE: '\x1b[37m',
            Color.BRIGHTBLACK: '\x1b[30;1m',
            Color.BRIGHTRED: '\x1b[31;1m',
            Color.BRIGHTGREEN: '\x1b[32;1m',
            Color.BRIGHTYELLOW: '\x1b[33;1m',
            Color.BRIGHTBLUE: '\x1b[34;1m',
            Color.BRIGHTMAGENTA: '\x1b[35;1m',
            Color.BRIGHTCYAN: '\x1b[36;1m',
            Color.BRIGHTWHITE: '\x1b[37;1m',
        }

    def print ( self, *message, **kwargs ):
        print (''.join ([self.__convert.get (x, str (x)) for x in message]), **kwargs)


class NoTTY:
    def __init__ ( self ):
        self.__colors = {
            Color.DEFAULT,
            Color.BLACK,
            Color.RED,
            Color.GREEN,
            Color.YELLOW,
            Color.BLUE,
            Color.MAGENTA,
            Color.CYAN,
            Color.WHITE,
            Color.BRIGHTBLACK,
            Color.BRIGHTRED,
            Color.BRIGHTGREEN,
            Color.BRIGHTYELLOW,
            Color.BRIGHTBLUE,
            Color.BRIGHTMAGENTA,
            Color.BRIGHTCYAN,
            Color.BRIGHTWHITE,
        }

    def print ( self, *message, **kwargs ):
        print (''.join ([str (x) for x in message if not x in self.__colors]), **kwargs)


class Log:
    class VERBOSE:
        pass
    class DEFAULT:
        pass
    class BRIEF:
        pass

    def __init__( self, policy ):
        # TODO: check os.env ('TERM') for terminal supports color
        self.__tty = VT100 () if sys.stdout.isatty () else NoTTY()
        self.__policy = policy

    policy = property (lambda self: self.__policy)

    debug = lambda self, *message, **kwargs: self.__print (*message, level_message="debug", level_color=Color.BRIGHTWHITE, **kwargs)
    info = lambda self, *message, **kwargs: self.__print (*message, level_message="info", level_color=Color.BRIGHTCYAN, **kwargs)
    notice = lambda self, *message, **kwargs: self.__print (*message, level_message="notice", level_color=Color.MAGENTA, **kwargs)
    warning = lambda self, *message, **kwargs: self.__print (*message, level_message="warning", level_color=Color.BRIGHTYELLOW, **kwargs)
    error = lambda self, *message, **kwargs: self.__print (*message, level_message="error", level_color=Color.BRIGHTRED, **kwargs)
    fatal = lambda self, *message, **kwargs: self.__print (*message, level_message="fatal", level_color=Color.BRIGHTRED, **kwargs)

    def __print ( self, *message, level_message, level_color, prefix=True, flush=True, **kwargs ):
        if prefix:
            message = ["[t:%s] " % level_message, level_color] \
                + list (message) \
                + [Color.DEFAULT]
        self.__tty.print (*message, flush=flush, **kwargs)

    def __call__ ( self, *args, **kwargs ):
        return self.info (*args, **kwargs)


# #!/usr/bin/env python3
# 
# import sys
# 
# def prepare():
#     if sys.platform == 'win32':  # if os is outdated
#         return prepare_windows ()
#     if sys.stdout.isatty ():
#         pass # ^_^
# 
# 
# # TODO: move into separate file
# def prepare_windows():
#     # Это выглядит как мерзкий, грязный хак, каковым является вообще любая работа с windows.
#     import ctypes
# 
#     STD_INPUT_HANDLE = -10
#     STD_OUTPUT_HANDLE = -11
#     STD_ERROR_HANDLE = -12
# 
#     FOREGROUND_BLUE = 0x01
#     FOREGROUND_GREEN = 0x02
#     FOREGROUND_RED = 0x04
#     FOREGROUND_INTENSITY = 0x08
#     BACKGROUND_BLUE = 0x10
#     BACKGROUND_GREEN = 0x20
#     BACKGROUND_RED = 0x40
#     BACKGROUND_INTENSITY = 0x80
#     windows_colors = [
#         0,  # black
#         FOREGROUND_RED,  # red
#         FOREGROUND_GREEN,  # green
#         FOREGROUND_GREEN | FOREGROUND_RED,  # brown
#         FOREGROUND_BLUE,  # blue
#         FOREGROUND_BLUE | FOREGROUND_RED,  # magenta
#         FOREGROUND_BLUE | FOREGROUND_GREEN,  # skyblue
#         FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_RED,  # gray
#         0, 0, 0
#     ]
# 
#     def windows_write( text, end='' ):
#         text += end
#         handle = ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
#         pieces = text.split('\x1b[')
#         sys.stdout.write(pieces[0])
#         sys.stdout.flush()
#         for str in pieces[1:]:
#             color, line = str.split('m', 1)
#             numbers = [int(x) for x in color.split(';')]
#             mask = 0
#             for x in numbers:
#                 if x == 0:
#                     mask |= windows_colors[7]
#                 if x == 1:
#                     mask |= FOREGROUND_INTENSITY
#                 if 30 <= x <= 39:
#                     mask |= windows_colors[x - 30]
#             ctypes.windll.kernel32.SetConsoleTextAttribute(handle, mask)
#             sys.stdout.write(line.encode('utf8').decode('ibm866'))
#             sys.stdout.flush()
# 
#     def windows_convert_tests( tests ):
#         pass
# 
#     log.write = windows_write
#     convert_tests = windows_convert_tests


