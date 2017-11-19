
class WolfConnection:
    def __init__( self ):
        self.__socket = socket.socket()
        self.__socket.connect(('127.0.0.1', 1917))
        self.__tail = b''
        self.__queue = iter([])

    def query( self, j ):
        self.__socket.send((json.dumps(j) + '\n').encode('utf-8'))
        while True:
            r = next(self.__queue, None)
            if r is not None:
                return r
            data = self.__socket.recv(4096).split(b'\n')
            self.__tail += data[0]
            queue = []
            for x in data[1:]:
                queue.append(json.loads(self.__tail.decode('utf-8')))
                self.__tail = x
            self.__queue = iter(queue)


def wolf_export( problem, configuration, global_config ):
    log.info("== upload problem %s" % configuration['id'])
    os.chdir(configuration['tests-directory'])
    if 'full' not in configuration:
        raise Error ("cannot full name for problem %s" % configuration['id'])
    checker = None
    for checker_name in [
        'check', 'checker', 'check_' + configuration['id'], 'checker_' + configuration['id']
    ]:
        checker = heuristic.source_find(os.path.join('..', checker_name))
        if checker is not None:
            break
    if checker is None:
        raise Error ('cannot find checker')
    wolf_compilers = {
        'delphi': 'win32.checker.delphi.ifmo',
        # 'delphi': 'win32.checker.delphi.kitten',
        'c++': 'win32.checker.c++',
        'perl': 'win32.perl'  # nothing special
    }
    checker_name = os.path.basename(checker)
    compiler = wolf_compilers[global_config.detect_language(checker).name]
    tests = [Test.file (x) for x in problem.tests]
    if not tests:
        raise T.Error('problem %s: no tests found' % problem)
    log('  name: %s' % configuration['id'])
    log('  full name: %s' % configuration['full'])
    log('  input file: %s' % configuration['input-file'])
    log('  output file: %s' % configuration['output-file'])
    log('  time limit: %s' % configuration['time-limit'])
    log('  memory limit: %s' % configuration['memory-limit'])
    log('  checker: %s (compiled with %s)' % (checker_name, compiler))
    log('tests (total: %d): %s' % (len(tests), ','.join(tests)))
    with open(checker, 'rb') as f:
        data = f.read()
        checker = base64.b64encode(data).decode('ascii')
    wolf = WolfConnection()
    r = wolf.query({'action': 'ping'})
    Error.ensure (r is True)
    log_write = lambda text: log (text, prefix=False, end='')
    log_write('send packets:')
    problem_id = wolf.query(
        {'action': 'problem.create', 'name': configuration['id'], 'full': configuration['full']}
    )
    Error.ensure (isinstance(problem_id, int))
    log_write('.')
    r = wolf.query({
        'action': 'problem.files.set', 'id': problem_id, 'input': configuration['input-file'],
        'output': configuration['output-file']
    })
    Error.ensure (r)
    log_write('.')
    r = wolf.query({
        'action': 'problem.limits.set', 'id': problem_id, 'time': configuration['time-limit'],
        'memory': configuration['memory-limit']
    })
    error.ensure (r)
    log_write('.')
    r = wolf.query({
        'action': 'problem.checker.set', 'id': problem_id, 'name': checker_name,
        'compiler': compiler, 'source': checker
    })
    Error.ensure (r)
    log_write('.')
    for test in tests:
        with open(test, 'rb') as f:
            data = f.read()
            input = base64.b64encode(data).decode('ascii')
        with open(test + '.a', 'rb') as f:
            data = f.read()
            answer = base64.b64encode(data).decode('ascii')
        r = wolf.query(
            {'action': 'problem.test.add', 'id': problem_id, 'test': input, 'answer': answer}
        )
        Error.ensure (r)
        log_write('.')
    log('', prefix='')
    log.info('uploaded, problem id: %d' % problem_id)


