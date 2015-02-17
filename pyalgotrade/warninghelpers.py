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

import warnings


class PyAlgoTradeDeprecationWarning(DeprecationWarning):
    pass

warnings.simplefilter("default", PyAlgoTradeDeprecationWarning)


# Deprecation warnings are disabled by default in Python 2.7, so this helper function enables them back.
def deprecation_warning(msg, stacklevel=0):
    warnings.warn(msg, category=PyAlgoTradeDeprecationWarning, stacklevel=stacklevel+1)
