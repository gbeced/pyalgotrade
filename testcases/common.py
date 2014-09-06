# PyAlgoTrade
#
# Copyright 2011-2014 Gabriel Martin Becedillas Ruiz
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

from pyalgotrade import dataseries


def run_and_get_output(cmd):
    return subprocess.check_output(cmd, universal_newlines=True, stderr=subprocess.STDOUT)


def run_python_code(code, outputFileName=None):
    cmd = ["python"]
    cmd.append("-u")
    cmd.append("-c")
    cmd.append(code)
    ret = run_and_get_output(cmd)
    if outputFileName:
        outputFile = open(outputFileName, "w")
        outputFile.write(ret)
        outputFile.close()
    return ret


def run_python_script(script, params=[]):
    cmd = ["python"]
    cmd.append("-u")
    cmd.append(script)
    cmd.extend(params)
    return run_and_get_output(cmd)


def run_sample_script(script, params=[]):
    lines = run_python_script(os.path.join("samples", script), params).split("\n")
    # Skip the last, empty line.
    return lines[:-1]


def get_file_lines(fileName):
    rawLines = open(fileName, "r").readlines()
    return [rawLine.strip() for rawLine in rawLines]


def compare_head(fileName, lines, path="samples"):
    assert(len(lines) > 0)
    fileLines = get_file_lines(os.path.join(path, fileName))
    return fileLines[0:len(lines)] == lines


def compare_tail(fileName, lines, path="samples"):
    assert(len(lines) > 0)
    fileLines = get_file_lines(os.path.join(path, fileName))
    return fileLines[len(lines)*-1:] == lines


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


def normalize_value(value, decimals):
    if value is not None:
        value = round(value, decimals)
    return value


def get_data_file_path(fileName):
    return os.path.join(os.path.split(__file__)[0], "data", fileName)


def test_from_csv(testcase, filename, filterClassBuilder, roundDecimals=2, maxLen=dataseries.DEFAULT_MAX_LEN):
    inputValues, expectedValues = load_test_csv(get_data_file_path(filename))
    inputDS = dataseries.SequenceDataSeries(maxLen=maxLen)
    filterDS = filterClassBuilder(inputDS)
    for i in xrange(len(inputValues)):
        inputDS.append(inputValues[i])
        value = normalize_value(filterDS[i], roundDecimals)
        expectedValue = normalize_value(expectedValues[i], roundDecimals)
        testcase.assertEqual(value, expectedValue)


def init_temp_path():
    storage = get_temp_path()
    if not os.path.exists(storage):
        os.mkdir(storage)


def get_temp_path():
    return "data"


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
