#!/usr/bin/env python3
# -*- coding: utf8 -*-
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

import sys
import argparse

from tlib import Color, Error, Log

import heuristic
import help
from wolf import wolf_export
from invoker import runner_choose
from settings import Settings


class T:
    def __init__ ( self, *, log_policy ):
        self.__log = Log (policy=log_policy)
        self.__configuration = heuristic.Configuration (
            testlib_checker_path = lambda checker: "/home/burunduk3/source/testlib/checkers/%s.cpp" % checker,
        t=self)
        self.__runner = None
        self.__defaults = Settings (
            limit_time = 5.0,
            limit_idle = 10.0,
            limit_memory = 1024 << 20,
            filename_input = Settings.STDIN,
            filename_output = Settings.STDOUT,
        )

    defaults = property (lambda self: self.__defaults)
    log = property (lambda self: self.__log)
    configuration = property (lambda self: self.__configuration)
    compilers = property (lambda self: self.__configuration.compilers)

    def error ( self, message, *, cls=Error ):
        return cls (message, t=self)

    def ensure ( self, expression, message ):
        if not expression:
            raise Error (message, t=self)

    def run_prepare ( self ):
        if self.__runner is None:
            self.__runner =  runner_choose (t=self) (t=self)

    def run ( self, *args, **kwargs ):
        self.run_prepare ()
        return self.__runner.run (*args, **kwargs)




class API:
    def __init__ ( self, *, arguments ):
        self.__arguments = arguments
        self.__t = T (log_policy=arguments.log_policy)
        self.__heuristics = heuristic.Heuristics (arguments=self.__arguments, t=self.__t)

        self.problem_build = (self.__target_problem, None, self.__problem_build)
        self.problem_clean = (self.__target_problem, None, self.__problem_clean)
        self.solution_check = (self.__target_problem, self.__option_solution, self.__solution_check)

    error = property (lambda self: self.__t.error)

    def __target_problem ( self ):
        if self.__arguments.recursive:
            yield from self.__heuristics.problem_search ()
        else:
            yield self.__heuristics.problem_open ()

    def __problem_build ( self, problem ):
        problem.build ()
        if problem.solution_model is None:
            self.__t.log.warning ('no model solution')
        elif not self.__solution_check (problem, problem.solution_model):
            raise self.__t.error ("build failed: model solution doesn't work")

    def __problem_clean ( self, problem ):
        problem.clean (remove_tests=not self.__arguments.keep_tests)

    def __solution_check ( self, problem, solution ):
        verdict = problem.solution_check (solution, self.__arguments.keep_going)
        if self.__t.log.policy is Log.BRIEF:
            self.__t.log (solution, ': ', Color.GREEN if verdict else Color.RED, verdict, Color.DEFAULT, " [%.2fs, %.2fMiB] " % (verdict.peak_time, verdict.peak_memory / 2**20), verdict.comment)
        return verdict

    def __option_solution ( self, options, *, target ):
        while len (options):
            option = options.pop ()
            yield self.__heuristics.solution_open (option, problem=target, defaults=self.__heuristics.defaults (target.defaults))


    # def __stress ( self, problem, arguments ):
    #     try:
    #         generator, solution = arguments[:2]
    #     except ValueError as error:
    #         raise Error ("usage: t.py stress <generator> <solution>") from error
    #     generator, solution = [heuristic.source_find (x) for x in (generator, solution)]
    #     r = True
    #     while r:
    #         r = check_problem (problem, solution=solution, tests=[
    #             Test.generate (generator, problem=problem, name='<stress>')
    #         ], quiet=True, t=self )

    # def __tests ( self, problem, *arguments ):
    #     tests_export (problem)

    # def __wolf_export ( self, problem, *arguments ):
    #     problem_configuration = self.__legacy.read_configuration (problem)
    #     wolf_export (problem, problem_configuration, self.__legacy)

    # def __problem_create ( self, uuid=None ):
    #     problem = Problem.new ()
    #     uuid = problem.create (uuid)
    #     self.__problems = [problem]
    #     self.__log ('create problem #%s' % uuid)

    # def __problem_reset ( self, problem, arguments ):
    #     problem.reset ()

    # def __problem_rescan ( self, problem, arguments ):
    #     heuristic.problem_rescan (problem, t=self)

    # def __problem_set ( self, problem, arguments ):
    #     raise Error ("TODO")

    # def __help ( self, par='disclaimer' ):
    #     sys.stdout.write ({
    #         'disclaimer': help.disclaimer,
    #         'gpl:c': help.license,
    #         'gpl:w': help.warranty,
    #     }[par])


def main ():
    parser = argparse.ArgumentParser (description='t.py: programming contest problem utility')
    parser.add_argument ('--recursive', '-r', dest='recursive', action='store_true', default=False)
    parser.add_argument ('--brief', '-b', dest='log_policy', action='store_const', const=Log.BRIEF, default=Log.DEFAULT)
    parser.add_argument ('--verbose', '-v', dest='log_policy', action='store_const', const=Log.VERBOSE, default=Log.DEFAULT)
    parser.add_argument ('--keep-going', '-k', dest='keep_going', action='store_true', default=False) # check on all tests
    parser.add_argument ('--keep-tests', '-t', dest='keep_tests', action='store_true', default=False) # remove tests on clean
    parser.add_argument ('--checker', dest='checker', default=None)
    parser.add_argument ('--limit-time', dest='limit_time', default=None)
    parser.add_argument ('--limit-idle', dest='limit_idle', default=None)
    parser.add_argument ('--limit-memory', dest='limit_memory', default=None)
    parser.add_argument ('--filename-input', dest='filename_input', default=None)
    parser.add_argument ('--filename-output', dest='filename_output', default=None)
    parser.add_argument (dest='commands', nargs='+')
    arguments = parser.parse_args ()

    # platform.prepare ()
    # heuristic.AutoGenerator.register (t=tpy)
    # languages = heuristic.compilers_configure ( configuration, tpy )
    # tpy.set_languages (languages)
    api = API (arguments=arguments)

    commands = arguments.commands
    while len (commands):
        command = commands.pop (0)
        # aliases
        command = {
            'build': 'problem:build',
            'clean': 'problem:clean',
            'check': 'solution:check',
            # 'tests': '???',
        }.get (command, command)
        
        try:
            targets, options, action = {
                'problem:build': api.problem_build,
                'problem:clean': api.problem_clean,
                'solution:check': api.solution_check,
            }[command]
        except KeyError:
            raise api.error ("unknown command: '%s'" % command) from None
        try:
            for target in targets ():
                target.info ()
                if options is None:
                    action (target)
                else:
                    for option in options (commands, target=target):
                        action (target, option)
        except NotImplementedError as error:
            raise api.error ("not implemented: " + str (error)) from None

        # actions = {
        #         ('check', self.__check),
        #         ('clean', self.__clean, None, False),
        #         ('stress', self.__stress),
        #         ('tests', self.__tests),
        #         # ('problem:reset', self.__problem_reset),
        #         # ('problem:rescan', self.__problem_rescan),
        #         # ('problem:set', self.__problem_set),
        #         ('wolf:export', self.__wolf_export)
        #     ]
        # }
        # actions.update ({
        #     'problem:create': lambda command, args: self.__problem_create (*args),
        #     'help': lambda command, args: self.__help (*args)
        # })


try:
    main ()
except Error as e:
    e.log ()
    sys.exit (1)
except KeyboardInterrupt:
    print ("^C")
    sys.exit (2)

