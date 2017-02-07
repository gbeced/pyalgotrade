# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import csv
import os
import shutil
import subprocess
import tempfile
import unittest

# Force matplotlib to not use any Xwindows backend.
import matplotlib
matplotlib.use('Agg')

from pyalgotrade import dataseries


class RunResults(object):
    def __init__(self, retcode, output):
        self.__retcode = retcode
        self.__output = output

    def exit_ok(self):
        return self.__retcode == 0

    def get_output(self):
        return self.__output

    def get_output_lines(self, skip_last_line_if_empty=False):
        ret = self.__output.splitlines()
        # Skip the last, empty line.
        if skip_last_line_if_empty and len(ret[:-1]) == 0:
            ret = ret[:-1]
        return ret


def run_cmd(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    output, unused_err = process.communicate()
    retcode = process.poll()
    return RunResults(retcode, output)


def run_python_code(code):
    cmd = ["python"]
    cmd.append("-u")
    cmd.append("-c")
    cmd.append(code)
    return run_cmd(cmd)


def run_sample_script(script, params=[]):
    cmd = ["python"]
    cmd.append("-u")
    cmd.append(os.path.join("samples", script))
    cmd.extend(params)
    return run_cmd(cmd)


def get_file_lines(fileName):
    rawLines = open(fileName, "r").read().splitlines()
    return [rawLine.strip() for rawLine in rawLines]


def compare_head(fileName, lines, path="samples"):
    assert(len(lines) > 0)
    fileLines = get_file_lines(os.path.join(path, fileName))
    return fileLines[0:len(lines)] == lines


def compare_tail(fileName, lines, path="samples"):
    assert(len(lines) > 0)
    fileLines = get_file_lines(os.path.join(path, fileName))
    return fileLines[len(lines)*-1:] == lines


def head_file(fileName, line_count, path="samples"):
    assert(line_count > 0)
    fileLines = get_file_lines(os.path.join(path, fileName))
    return fileLines[0:line_count]


def tail_file(fileName, line_count, path="samples"):
    assert(line_count > 0)
    lines = get_file_lines(os.path.join(path, fileName))
    return lines[line_count*-1:]


def load_test_csv(path):
    inputSeq = []
    expectedSeq = []
    csvFile = open(path, "r")
    reader = csv.DictReader(csvFile)
    for row in reader:
        inputSeq.append(float(row["Input"]))
        expected = row["Expected"]
        if not expected:
            expected = None
        else:
            expected = float(expected)
        expectedSeq.append(expected)

    return inputSeq, expectedSeq


def get_data_file_path(fileName):
    return os.path.join(os.path.split(__file__)[0], "data", fileName)


def test_from_csv(testcase, filename, filterClassBuilder, roundDecimals=2, maxLen=None):
    inputValues, expectedValues = load_test_csv(get_data_file_path(filename))
    inputDS = dataseries.SequenceDataSeries(maxLen=maxLen)
    filterDS = filterClassBuilder(inputDS)
    for i in xrange(len(inputValues)):
        inputDS.append(inputValues[i])
        value = safe_round(filterDS[i], roundDecimals)
        expectedValue = safe_round(expectedValues[i], roundDecimals)
        testcase.assertEqual(value, expectedValue)


def safe_round(number, ndigits):
    ret = None
    if number is not None:
        ret = round(number, ndigits)
    return ret


class CopyFiles:
    def __init__(self, files, dst):
        self.__files = files
        self.__dst = dst
        self.__toRemove = []

    def __enter__(self):
        for src in self.__files:
            shutil.copy2(src, self.__dst)
            if os.path.isdir(self.__dst):
                self.__toRemove.append(os.path.join(self.__dst, os.path.basename(src)))
            else:
                self.__toRemove.append(self.__dst)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for src in self.__toRemove:
            os.remove(src)


class TmpDir(object):
    def __init__(self):
        self.__tmpdir = None

    def __enter__(self):
        self.__tmpdir = tempfile.mkdtemp()
        return self.__tmpdir

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.__tmpdir is not None:
            shutil.rmtree(self.__tmpdir)


class TestCase(unittest.TestCase):
    pass
