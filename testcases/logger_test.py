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

import datetime

from testcases import common


class TestCase(common.TestCase):
    # Check that strategy and custom logs have the proper datetime, this is, the bars date time.
    def testBacktestingLog1(self):
            code = """from testcases import logger_test_1
logger_test_1.main()
"""
            res = common.run_python_code(code)
            expectedLines = [
                "2000-01-01 00:00:00 strategy [INFO] bla",
                "2000-01-01 00:00:00 custom [INFO] ble",
            ]
            self.assertEqual(res.get_output_lines(), expectedLines)
            self.assertTrue(res.exit_ok())

    # Check that strategy and custom logs have the proper datetime, this is, the bars date time.
    def testBacktestingLog2(self):
            code = """from testcases import logger_test_2
logger_test_2.main()
"""
            res = common.run_python_code(code)
            self.assertEqual(len(res.get_output_lines()), 3)
            self.assertEqual(res.get_output_lines()[0], "2000-01-01 00:00:00 strategy [INFO] bla")
            self.assertEqual(
                res.get_output_lines()[1],
                "2000-01-02 00:00:00 broker.backtesting [DEBUG] Not enough cash to fill orcl order [1] for 1 share/s"
            )
            self.assertEqual(res.get_output_lines()[2], "2000-01-02 00:00:00 strategy [INFO] bla")
            self.assertTrue(res.exit_ok())

    # Check that strategy and custom logs have the proper datetime, this is, the current date.
    def testNonBacktestingLog3(self):
            code = """from testcases import logger_test_3
logger_test_3.main()
"""
            res = common.run_python_code(code)

            now = datetime.datetime.now()
            self.assertEqual(len(res.get_output_lines()), 2)
            for line in res.get_output_lines(True):
                self.assertEqual(line.find(str(now.date())), 0)
            self.assertNotEqual(res.get_output_lines()[0].find("strategy [INFO] bla"), -1)
            self.assertNotEqual(res.get_output_lines()[1].find("custom [INFO] ble"), -1)
            self.assertTrue(res.exit_ok())
