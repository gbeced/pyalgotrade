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

from pyalgotrade import dataseries
from pyalgotrade.bar import Frequency
from pyalgotrade.instrument import build_instrument

import six


class BarDataSeries(dataseries.SequenceDataSeries):
    """A DataSeries of :class:`pyalgotrade.bar.Bar` instances. All bars must have the same frequency.

    :param instrument: Instrument identifier.
    :type instrument: A :class:`pyalgotrade.instrument.Instrument` or a string formatted like
            QUOTE_SYMBOL/PRICE_CURRENCY.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """

    def __init__(self, instrument, maxLen=None):
        super(BarDataSeries, self).__init__(maxLen)
        self._instrument = build_instrument(instrument)
        self._openDS = dataseries.SequenceDataSeries(maxLen)
        self._closeDS = dataseries.SequenceDataSeries(maxLen)
        self._highDS = dataseries.SequenceDataSeries(maxLen)
        self._lowDS = dataseries.SequenceDataSeries(maxLen)
        self._volumeDS = dataseries.SequenceDataSeries(maxLen)
        self._adjCloseDS = dataseries.SequenceDataSeries(maxLen)
        self._extraDS = {}
        self._useAdjustedValues = False

    def _getOrCreateExtraDS(self, name):
        ret = self._extraDS.get(name)
        if ret is None:
            ret = dataseries.SequenceDataSeries(self.getMaxLen())
            self._extraDS[name] = ret
        return ret

    def getInstrument(self):
        return self._instrument

    def setUseAdjustedValues(self, useAdjusted):
        self._useAdjustedValues = useAdjusted

    def append(self, bar):
        self.appendWithDateTime(bar.getDateTime(), bar)

    def appendWithDateTime(self, dateTime, bar):
        assert(dateTime is not None)
        assert(bar is not None)
        bar.setUseAdjustedValue(self._useAdjustedValues)

        # Check that all bars have the same instrument and frequency.
        assert self._instrument == bar.getInstrument()

        # Check that bars are not served out of order.
        if len(self):
            prev_bar = self[-1]

            assert bar.getFrequency() == prev_bar.getFrequency(), "Bars have different frequency"

            if bar.getDateTime() < prev_bar.getDateTime():
                raise Exception(
                    "%s bars are not in order. Previous datetime was %s and current datetime is %s" % (
                        bar.getInstrument(), prev_bar.getDateTime(), bar.getDateTime()
                    ))
            # Only Trade bars can have duplicate datetimes.
            elif bar.getDateTime() == prev_bar.getDateTime() and bar.getFrequency() != Frequency.TRADE:
                raise Exception(
                    "%s bars are not in order. Previous datetime was %s and current datetime is %s" % (
                        bar.getInstrument(), prev_bar.getDateTime(), bar.getDateTime()
                    ))

        super(BarDataSeries, self).appendWithDateTime(dateTime, bar)

        self._openDS.appendWithDateTime(dateTime, bar.getOpen())
        self._closeDS.appendWithDateTime(dateTime, bar.getClose())
        self._highDS.appendWithDateTime(dateTime, bar.getHigh())
        self._lowDS.appendWithDateTime(dateTime, bar.getLow())
        self._volumeDS.appendWithDateTime(dateTime, bar.getVolume())
        self._adjCloseDS.appendWithDateTime(dateTime, bar.getAdjClose())

        # Process extra columns.
        for name, value in six.iteritems(bar.getExtraColumns()):
            extraDS = self._getOrCreateExtraDS(name)
            extraDS.appendWithDateTime(dateTime, value)

    def getOpenDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the open prices."""
        return self._openDS

    def getCloseDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the close prices."""
        return self._closeDS

    def getHighDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the high prices."""
        return self._highDS

    def getLowDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the low prices."""
        return self._lowDS

    def getVolumeDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the volume."""
        return self._volumeDS

    def getAdjCloseDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the adjusted close prices."""
        return self._adjCloseDS

    def getPriceDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the close or adjusted close prices."""
        if self._useAdjustedValues:
            return self._adjCloseDS
        else:
            return self._closeDS

    def getExtraDataSeries(self, name):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` for an extra column."""
        return self._getOrCreateExtraDS(name)
