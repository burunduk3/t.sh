import os
import signal
import time
import threading

class RunResult:
  RUNTIME, TIME_LIMIT, MEMORY_LIMIT, OK = range(4)
  def __init__( self, result, exitcode, comment='' ):
    self.result, self.exitcode, self.comment = result, exitcode, comment

class Invoker:
    def __init__( self, executable, *, limit_time, limit_idle, limit_memory, t ):
        self.__executable = executable
        self.__limit_time = limit_time
        self.__limit_idle = limit_idle
        self.__limit_memory = limit_memory
        self.__process = None
        self.__condition = None
        self._t = t

    def __waiter( self ):
        self.__process.communicate()
        self.__condition.acquire()
        self.__condition.notify()
        self.__condition.release()

    def run( self, *, directory=None, stdin=None, stdout=None, stderr=None ):
    # limit resources of current process: bad idea
    # resource.setrlimit(resource.RLIMIT_CPU, ((int)(self.limit_time + 2), -1))
    # resource.setrlimit(resource.RLIMIT_DATA, (self.limit_memory, -1))
        start = time.time ()
        self.__process = self.__executable.start (directory=directory, stdin=stdin, stdout=stdout, stderr=stderr)
        pid = self.__process.pid
        self.__condition = threading.Condition()
        thread = threading.Thread(target=self.__waiter)
        # wait, what?
        thread.start()
        force_result = None
        while True:
            self.__condition.acquire()
            self.__condition.wait(0.01)
            self.__condition.release()
            if self.__process.returncode is not None:
                break
            try: # так может случится, что процесс завершится в самый интересный момент
                stat = open("/proc/%d/stat" % pid, 'r')
                stats = stat.readline().split()
                stat.close()
                stat = open("/proc/%d/statm" % pid, 'r')
                stats_m = stat.readline().split()
                stat.close()
                cpu_time = (int(stats[13]) + int(stats[14])) / os.sysconf (os.sysconf_names['SC_CLK_TCK'])
                mem_usage = int(stats_m[0]) * 1024
                line = "%.3f" % (time.time() - start)
                line = line + '\b' * len(line)
                self._t.log (line, prefix=False, end='')
                if cpu_time > self.__limit_time:
                    force_result = RunResult (RunResult.TIME_LIMIT, -1, 'cpu usage: %.2f' % cpu_time)
                    self.__process.terminate()
                if mem_usage > self.__limit_memory:
                    force_result = RunResult(RunResult.MEMORY_LIMIT, -1, 'memory usage: %d' % mem_usage)
                    self.__process.terminate()
            except IOError:
                pass
        line = "[%.3f] " % (time.time() - start)
        self._t.log (line, prefix=False, end='')
        if force_result is not None:
            return force_result
        code = self.__process.returncode
        if code == -signal.SIGXCPU:
            return RunResult(RunResult.TIME_LIMIT, code, 'signal SIGXCPU received')
        elif code != 0:
            return RunResult(RunResult.RUNTIME, code, 'runtime error %d' % code)
        else:
            return RunResult(RunResult.OK, code)

