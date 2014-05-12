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

import unittest
import datetime
from testcases import common


class TestCase(unittest.TestCase):
    # Check that strategy and custom logs have the proper datetime, this is, the bars date time.
    def testBacktestingLog1(self):
            code = """from testcases import logger_test_1
logger_test_1.main()
"""
            lines = common.run_python_code(code).split("\n")
            expectedLines = [
                "2000-01-01 00:00:00 strategy [INFO] bla",
                "2000-01-01 00:00:00 custom [INFO] ble",
                "",
            ]
            self.assertEqual(lines, expectedLines)

    # Check that strategy and custom logs have the proper datetime, this is, the bars date time.
    def testBacktestingLog2(self):
            code = """from testcases import logger_test_2
logger_test_2.main()
"""
            lines = common.run_python_code(code).split("\n")
            self.assertEqual(len(lines), 4)
            self.assertEqual(lines[0], "2000-01-01 00:00:00 strategy [INFO] bla")
            self.assertEqual(lines[1], "2000-01-02 00:00:00 broker.backtesting [DEBUG] Not enough cash to fill orcl order [1] for 1 share/s")
            self.assertEqual(lines[2], "2000-01-02 00:00:00 strategy [INFO] bla")
            self.assertEqual(lines[3], "")

    # Check that strategy and custom logs have the proper datetime, this is, the current date.
    def testNonBacktestingLog3(self):
            code = """from testcases import logger_test_3
logger_test_3.main()
"""
            lines = common.run_python_code(code).split("\n")

            now = datetime.datetime.now()
            self.assertEqual(len(lines), 3)
            for line in lines[:-1]:
                self.assertEqual(line.find(str(now.date())), 0)
            self.assertNotEqual(lines[0].find("strategy [INFO] bla"), -1)
            self.assertNotEqual(lines[1].find("custom [INFO] ble"), -1)
