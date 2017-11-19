import os

suffixes = {
    'c': 'c',
    'pas': 'pascal', 'dpr': 'delphi',
    'java': 'java', 'pl': 'perl', 'py': detector_python, 'sh': 'bash'
}


def suffixes_all ():
    return suffixes.keys ()

def tests_export ( problem ):
    os.chdir (problem.path)
    if not problem.tests:
        problem.research_tests ()
    tests = [Test.file (x) for x in problem.tests]
    if not tests:
        raise Error ('[problem %s]: no tests found' % problem.name)
    if not os.path.isdir ('tests'):
        os.mkdir ('tests')
    pattern = '%02d'
    if len (tests) >= 100:
        pattern = '%03d'
    if len (tests) >= 1000:
        raise Error ("[problem %s]: too many tests (%d)" % (problem.name, len (tests)))
    n = 0
    for i, x in enumerate (tests):
        test = x.create ()
        name = pattern % (i + 1)
        shutil.copy (test, os.path.join ('tests', name))
        shutil.copy (test + '.a', os.path.join ('tests', name) + '.a')
        n += 1
    log ('pattern: %s, tests copied: %d' % (pattern, n))




