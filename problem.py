#!/usr/bin/env python3

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

import os
import os.path
import shutil
import subprocess

from tlib import Module, Log
from compilers import CompilationError
from settings import Settings
from test import Answer
from verdict import Verdict

class Problem (Module):
    def __init__ (
        self, path, *args, id,
        generator=None,
        validator=None,
        interactor=None,
        checker=None,
        cleaner=None,
        solution_model=None,
        directory_source=None,
        directory_temp=None,
        directory_tests=None,
        defaults,
        sources=[],
        garbage=[],
        **kwargs
    ):
        super (Problem, self).__init__ (*args, **kwargs)
        self.__path = path
        self.__path_canonical = os.path.abspath (path)
        self.__id = id
        self.__generator = generator
        self.__validator = validator
        self.__interactor = interactor
        self.__checker = checker
        self.__cleaner = cleaner
        self.__solution_model = solution_model
        self.__directory_source = directory_source
        self.__directory_temp = directory_temp
        self.__directory_tests = directory_tests
        self.__defaults = defaults
        self.__sources = sources
        self.__garbage = garbage
        self.__tests = None

    generator = property (lambda self: self.__generator)
    @generator.setter
    def generator ( self, value ):
        self.__generator = value

    validator = property ()
    @validator.setter
    def validator ( self, value ):
        self.__validator = value

    interactor = property ()
    @interactor.setter
    def interactor ( self, value ):
        self.__interactor = value

    checker = property ()
    @checker.setter
    def checker ( self, value ):
        self.__checker = value

    cleaner = property ()
    @cleaner.setter
    def cleaner ( self, value ):
        self.__cleaner = value

    solution_model = property (lambda self: self.__solution_model)
    @solution_model.setter
    def solution_model ( self, value ):
        self.__solution_model = value

    defaults = property (lambda self: self.__defaults)
    tests = property (lambda self: self.__tests)
    @tests.setter
    def tests ( self, value ):
        self.__tests = value

    def __str__ ( self ):
        return self.__id

    def info ( self ):
        if self._log.policy is Log.BRIEF:
            self._log ("problem: %s" % self.__id)
            return
        self._log ('== problem “%s” ==' % self.__id)
        nop = lambda x: x
        def humansize ( x ):
            k = 1
            for suffix in ['', 'KiB', 'MiB', 'GiB', 'TiB']:
                if x < k * 1000 or suffix == 'TiB':
                    if suffix == '':
                        return "%d" % x
                    else:
                        return "%.2f %s" % (x / k, suffix)
                k *= 1024
        for name, value, filt in [
            ('path', self.__path_canonical, nop),
            ('time limit', self.__defaults.limit_time, nop),
            ('memory limit', self.__defaults.limit_memory, humansize),
            ('generator', self.__generator, nop),
            ('validator', self.__validator, nop),
            ('checker', self.__checker, nop),
            ('solution', self.__solution_model, nop),
            ('input', self.__defaults.filename_input, nop),
            ('output', self.__defaults.filename_output, nop),
        ]:
            if value is None:
                continue
            self._log ('  * %s: %s' % (name, filt (value)))

    def build ( self ):
        self._t.run_prepare ()
        dir_old = os.getcwd ()
        os.chdir (self.__path_canonical)
        try:
            if self._log.policy is not Log.BRIEF:
                self._log ('== build “%s” ==' % self.__id)
            if self.__solution_model is None:
                self._log.warning ('model solution not set')
            self._t.ensure (self.__generator is not None, "[problem %s]: no generator" % self.__id)
            self.__tests = self.__generator.run ()
            if self._log.policy is not Log.BRIEF:
                self._log ("total tests: %d" % len (self.__tests))
            self.testset_validate ()
            self.testset_answers ()
            if self._log.policy is Log.BRIEF:
                self._log ("build finished, total tests: %d" % len (self.__tests))
        finally:
            os.chdir (dir_old)

    def clean ( self, remove_tests=True ):
        self._t.run_prepare ()
        dir_old = os.getcwd ()
        os.chdir (self.__path_canonical)
        try:
            if self._log.policy is not Log.BRIEF:
                self._log ('== clean “%s” ==' % self.__id)
            try:
                for filename in os.listdir (self.__directory_temp):
                    os.remove (os.path.join (self.__directory_temp, filename))
                os.rmdir (self.__directory_temp)
            except FileNotFoundError:
                pass
            if self.__cleaner is not None:
                result = self.__cleaner.run ()
                if not result:
                    self._log.error ('cleaner failed: ', result)
                return
            if remove_tests:
                if self.__tests is not None:
                    for test in self.__tests:
                        os.remove (test.path)
                        os.remove (test.answer.path)
                if self.__directory_tests is not None and self.__directory_tests != self.__directory_source:
                    try:
                        os.rmdir (self.__directory_tests)
                    except FileNotFoundError:
                        pass
            for source in self.__sources:
                if source is None:
                    continue
                if source.executable is None:
                    continue
                if source.path == source.executable.path:
                    continue
                os.remove (source.executable.path)
            for filename in self.__garbage:
                try:
                    os.remove (filename)
                except FileNotFoundError:
                    pass
        finally:
            os.chdir (dir_old)

    def testset_validate ( self ):
        self._t.run_prepare ()
        if self.__validator is None:
            return self._log.warning ("validator not set")
        self.__validator.compile ()
        if self._log.policy is not Log.BRIEF:
            self._log ('validate tests', end='')
        for test in self.__tests:
            if self._log.policy is not Log.BRIEF:
                self._log ('.', prefix=False, end='')
            result = self.__validator.run ([test.path], stdin=test.path)
            if not result:
                raise self._error ('validation failed: %s' % (test))
        if self._log.policy is not Log.BRIEF:
            self._log ('done', prefix=False)

    def testset_answers ( self ):
        """ generate answers using model solution """
        self._t.run_prepare ()
        solution = self.__solution_model
        if solution is not None:
            solution.compile ()
            if self.__interactor is not None:
                self.__interactor.compile ()
            input_name = os.path.join (self.__directory_temp, solution.filename_input if type (solution.filename_input) is str else 'input')
            output_name = os.path.join (self.__directory_temp, solution.filename_output if type (solution.filename_output) is str else 'output')

        try:
            os.mkdir (self.__directory_temp)
        except FileExistsError:
            pass

        if self._log.policy is not Log.BRIEF:
            self._log ('generate answers', end='')
        for test in self.__tests:
            if test.answer is not None:
                if self._log.policy is not Log.BRIEF:
                    self._log ('+', prefix=False, end='')
                continue
            if self._log.policy is not Log.BRIEF:
                self._log ('.', prefix=False, end='')
            if solution is None:
                raise self._error ('no solution')
            shutil.copy (test.path, input_name)
            result_interactor = True
            if self.__interactor is not None:
                pipe_sr, pipe_iw = os.pipe ()
                pipe_ir, pipe_sw = os.pipe ()
                interactor = self.__interactor.run (
                    [os.path.basename (input_name), os.path.basename (output_name)],
                    wait=False,
                    directory=self.__directory_temp,
                    stdin=pipe_ir, stdout=pipe_iw
                )
                (result_interactor, result) = solution.run (
                    directory=self.__directory_temp,
                    interactor=interactor,
                    stdin=pipe_sr, stdout=pipe_sw
                )
            else:
                result = solution.run (
                    directory=self.__directory_temp,
                    stdin=None if type (solution.filename_input) is str else input_name,
                    stdout=None if type (solution.filename_output) is str else output_name,
                )
            if not result_interactor or not result:
                raise self._error ("solution failed [test: %s]: %s" % (test, result))
            shutil.copy (output_name, test.path + '.a')
            test.answer = Answer (test.path + '.a', test)
        if self._log.policy is not Log.BRIEF:
            self._log ('done', prefix=False)

    def solution_check ( self, solution, keep_going=False ):
        assert solution is not None
        self._t.run_prepare ()
        dir_old = os.getcwd ()
        os.chdir (self.__path_canonical)
        try:
            if self._log.policy is not Log.BRIEF:
                self._log ('== check “%s” solution: %s ==' % (self.__id, solution))
            if self.__tests is None:
                raise self._error ("no tests")
            if self.__checker is None:
                raise self._error ("no checker")
            self.__checker.compile ()
            try:
                solution.compile ()
            except CompilationError as error:
                if self._log.policy is Log.BRIEF:
                    return Verdict.ce ()
                raise error from error
            if self.__interactor is not None:
                self.__interactor.compile ()

            try:
                os.mkdir (self.__directory_temp)
            except FileExistsError:
                pass

            input_name = os.path.join (self.__directory_temp, solution.filename_input if type (solution.filename_input) is str else 'input')
            output_name = os.path.join (self.__directory_temp, solution.filename_output if type (solution.filename_output) is str else 'output')

            verdict = None
            peak_time = None
            peak_memory = None
            for i, test in enumerate (self.__tests):
                shutil.copy (test.path, input_name)
                if self._log.policy is not Log.BRIEF:
                    self._log ('test #%d [%s] ' % (i, test.path), end='')
                result_interactor = True
                # self._log.debug ('run with interactor: ', self.__interactor)
                if self.__interactor is not None:
                    pipe_sr, pipe_iw = os.pipe ()
                    pipe_ir, pipe_sw = os.pipe ()
                    interactor = self.__interactor.run (
                        [os.path.basename (input_name), os.path.basename (output_name)],
                        wait=False,
                        directory=self.__directory_temp,
                        stdin=pipe_ir, stdout=pipe_iw
                    )
                    (result_interactor, result) = solution.run (
                        directory=self.__directory_temp,
                        interactor=interactor,
                        stdin=pipe_sr, stdout=pipe_sw,
                        verbose=self._log.policy is not Log.BRIEF,
                        limit_time=solution.limit_time,
                        limit_idle=solution.limit_idle,
                        limit_memory=solution.limit_memory
                    )
                else:
                    result = solution.run (
                        directory=self.__directory_temp,
                        stdin=None if type (solution.filename_input) is str else input_name,
                        stdout=None if type (solution.filename_output) is str else output_name,
                        verbose=self._log.policy is not Log.BRIEF,
                        limit_time=solution.limit_time,
                        limit_idle=solution.limit_idle,
                        limit_memory=solution.limit_memory
                    )
                if peak_time is None or (result.time, i) > peak_time:
                    peak_time = (result.time, i)
                if peak_memory is None or (result.memory, i) > peak_memory:
                    peak_memory = (result.memory, i)
                if self._log.policy is not Log.BRIEF:
                    self._log ('* ', prefix=False, end='')
                if not result_interactor:
                    if self._log.policy is not Log.BRIEF:
                        self._log.error ("rejected by interactor: %s" % result_interactor)
                    if verdict is None:
                        verdict = Verdict.fail_solution (i + 1, result, peak_time=peak_time[0], peak_memory=peak_memory[0])
                    if not keep_going:
                        return verdict
                    continue
                if not result:
                    if self._log.policy is not Log.BRIEF:
                        self._log.error ('rejected: %s' % result)
                    if verdict is None:
                        verdict = Verdict.fail_solution (i + 1, result, peak_time=peak_time[0], peak_memory=peak_memory[0])
                    if not keep_going:
                        return verdict
                    continue
                result = self.__checker.run ([input_name, output_name, test.answer.path], stderr=subprocess.PIPE)
                if self._log.policy is not Log.BRIEF:
                    self._log (result.stderr.strip (), prefix=False)
                if not result:
                    if self._log.policy is not Log.BRIEF:
                        self._log.error ('rejected by checker: %s' % result)
                    if verdict is None:
                        verdict = Verdict.fail_checker (i + 1, result, result.stderr.strip (), peak_time=peak_time[0], peak_memory=peak_memory[0])
                    if not keep_going:
                        return verdict
                    continue
            if verdict is None:
                verdict = Verdict.ok (peak_time=peak_time[0], peak_memory=peak_memory[0])
            return verdict
        finally:
            os.chdir (dir_old)


