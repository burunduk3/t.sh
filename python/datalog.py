import time

class Type:
    def __init__ ( self, t ):
        self._t = t
    def __str__ ( self ):
        assert False
    def dump ( self ):
        assert False
    def __eq__ ( self, x ):
        assert False

class Datalog:
    def __init__ ( self, datalog, actions={}, *, create=False, t ):
        self._t = t
        self._actions = actions
        self._time = 0
        if not create:
            try:
                with open (datalog, 'r') as log:
                    for line in log.readlines ():
                        self.__event (line)
            except FileNotFoundError:
                self._t.log.warning ("file not found: '%s', create new" % datalog)
            self.__datalog = open (datalog, 'a')
        else:
            self.__datalog = open (datalog, 'x')

    def __precheck ( self, line ):
        data = line.split ()
        if self._time > int(data[0]):
            return None
        event = data[1]
        if event not in self._actions:
            return None
        return True
    def __event ( self, line ):
        data = line.split ()
        self._time = int(data[0])
        event = data[1]
        return self._actions[event] (*data[2:])
    def _commit ( self, *args, check=True ):
        now = str (int (time.time ()))
        line = ' '.join ([now] + list (args)) # TODO: spaces and so on
        if self.__precheck (line) is None:
            assert not check
            return None
        print (line, file=self.__datalog)
        self.__datalog.flush ()
        return self.__event (line)

