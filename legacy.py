
class Configuration:
    def __init__( self ):
        self.compilers = {}
        self.detector = {}

    def detect_language( self, source ):
        if source.endswith('Check.java'):
            return self.compilers["java.checker"]
        suffix = os.path.splitext(source)[1][1:]
        if suffix not in self.detector:
            return None
        detector = self.detector[suffix]
        if type(detector) == str:
            return self.compilers[detector]
        return self.compilers[detector(source)]

    @staticmethod
    def read_configuration( path ):
        problem_name = os.path.basename(os.path.abspath(path))
        configuration = {'path': path, 'id': problem_name}
        ppfile = os.path.join(path, 'problem.properties')
        if os.path.isfile(ppfile):
            configuration.update(read_problem_properties(ppfile))
        for name, value in [
            ('input-file', problem_name + '.in'),
            ('output-file', problem_name + '.out'),
            ('time-limit', 5.0),
            ('memory-limit', 768 * 2**20)
        ]:
            if name in configuration:
                continue
            log.warning("%s isn't set for problem %s, using default (%s)" %
                (name, configuration['id'], repr(value)))
            configuration[name] = value
            configuration['time-limit'] = float(configuration['time-limit'])
        for name in ['memory-limit']:
            for suffix, multiplier in [
                ('K', 2**10), ('M', 2**20), ('G', 2**30), ('T', 2**40), ('', 1)
            ]:
                if isinstance(configuration[name], str) and configuration[name].endswith(suffix):
                    configuration[name] = int(configuration[name].replace(suffix, '')) * multiplier
        if 'source-directory' not in configuration:
            for directory in ['source', 'src', 'tests']:
                if os.path.isdir(os.path.join(path, directory)):
                    configuration.update({'source-directory': os.path.join(path, directory)})
                    break
        if 'tests-directory' not in configuration:
            configuration.update({'tests-directory': os.path.join(path, 'tests')})
        return configuration

