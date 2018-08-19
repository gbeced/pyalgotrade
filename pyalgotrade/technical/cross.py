# PyAlgoTrade
#
# Copyright 2011-2018 Gabriel Martin Becedillas Ruiz
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


def compute_diff(values1, values2):
    assert(len(values1) == len(values2))
    ret = []
    for i in range(len(values1)):
        v1 = values1[i]
        v2 = values2[i]
        if v1 is not None and v2 is not None:
            diff = v1 - v2
        else:
            diff = None
        ret.append(diff)
    return ret


def _get_stripped(values1, values2, alignLeft):
    if len(values1) > len(values2):
        if alignLeft:
            values1 = values1[0:len(values2)]
        else:
            values1 = values1[len(values1)-len(values2):]
    elif len(values2) > len(values1):
        if alignLeft:
            values2 = values2[0:len(values1)]
        else:
            values2 = values2[len(values2)-len(values1):]
    return values1, values2


def _cross_impl(values1, values2, start, end, signCheck):
    # Get both set of values.
    values1, values2 = _get_stripped(values1[start:end], values2[start:end], start > 0)

    # Compute differences and check sign changes.
    ret = 0
    diffs = compute_diff(values1, values2)
    diffs = filter(lambda x: x != 0, diffs)
    prevDiff = None
    for diff in diffs:
        if prevDiff is not None and not signCheck(prevDiff) and signCheck(diff):
            ret += 1
        prevDiff = diff
    return ret


# Note:
# Up to version 0.12 CrossAbove and CrossBelow were DataSeries.
# In version 0.13 SequenceDataSeries was refactored to support specifying a limit to the amount
# of values to hold. This was introduced mainly to reduce memory footprint.
# This change had a huge impact on the way DataSeries filters were implemented since they were
# mosly views and didn't hold any actual values. For example, a SMA(200) didn't hold any values at all
# but rather calculate those on demand by requesting 200 values from the DataSeries being wrapped.
# Now that the DataSeries being wrapped may not hold so many values, DataSeries filters were refactored
# to an event based model and they will calculate and hold resulting values as new values get added to
# the underlying DataSeries (the one being wrapped).
# Since it was too complicated to make CrossAbove and CrossBelow filters work with this new model (
# mainly because the underlying DataSeries may not get new values added at the same time, or one after
# another) I decided to turn those into functions, cross_above and cross_below.

def cross_above(values1, values2, start=-2, end=None):
    """Checks for a cross above conditions over the specified period between two DataSeries objects.

    It returns the number of times values1 crossed above values2 during the given period.

    :param values1: The DataSeries that crosses.
    :type values1: :class:`pyalgotrade.dataseries.DataSeries`.
    :param values2: The DataSeries being crossed.
    :type values2: :class:`pyalgotrade.dataseries.DataSeries`.
    :param start: The start of the range.
    :type start: int.
    :param end: The end of the range.
    :type end: int.

    .. note::
        The default start and end values check for cross above conditions over the last 2 values.
    """
    return _cross_impl(values1, values2, start, end, lambda x: x > 0)


def cross_below(values1, values2, start=-2, end=None):
    """Checks for a cross below conditions over the specified period between two DataSeries objects.

    It returns the number of times values1 crossed below values2 during the given period.

    :param values1: The DataSeries that crosses.
    :type values1: :class:`pyalgotrade.dataseries.DataSeries`.
    :param values2: The DataSeries being crossed.
    :type values2: :class:`pyalgotrade.dataseries.DataSeries`.
    :param start: The start of the range.
    :type start: int.
    :param end: The end of the range.
    :type end: int.

    .. note::
        The default start and end values check for cross below conditions over the last 2 values.
    """
    return _cross_impl(values1, values2, start, end, lambda x: x < 0)
