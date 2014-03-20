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

import os

from pyalgotrade import dispatcher
from pyalgotrade.dataseries import resampled

datetime_format = "%Y-%m-%d %H:%M:%S"


class CSVFileWriter(object):
    def __init__(self, csvFile):
        self.__file = open(csvFile, "w")
        self.__writeLine("Date Time", "Open", "High", "Low", "Close", "Volume", "Adj Close")

    def __writeLine(self, *values):
        line = ",".join([str(value) for value in values])
        self.__file.write(line)
        self.__file.write(os.linesep)

    def writeSlot(self, slot):
        adjClose = slot.getAdjClose()
        if adjClose is None:
            adjClose = ""
        dateTime = slot.getDateTime().strftime(datetime_format)
        self.__writeLine(dateTime, slot.getOpen(), slot.getHigh(), slot.getLow(), slot.getClose(), slot.getVolume(), adjClose)

    def close(self):
        self.__file.close()


class Sampler(object):
    def __init__(self, barFeed, frequency, csvFile):
        instruments = barFeed.getRegisteredInstruments()
        if len(instruments) != 1:
            raise Exception("Only barfeeds with 1 instrument can be resampled")

        barFeed.getNewBarsEvent().subscribe(self.__onBars)
        self.__barFeed = barFeed
        self.__frequency = frequency
        self.__instrument = instruments[0]
        self.__slot = None
        self.__writer = CSVFileWriter(csvFile)

    def __onBars(self, dateTime, bars):
        slotDateTime = resampled.get_slot_datetime(dateTime, self.__frequency)
        bar = bars[self.__instrument]

        if self.__slot is None:
            self.__slot = resampled.Slot(slotDateTime, bar, self.__frequency)
        elif self.__slot.getDateTime() == slotDateTime:
            self.__slot.addBar(bar)
        else:
            self.__writer.writeSlot(self.__slot)
            self.__slot = resampled.Slot(slotDateTime, bar, self.__frequency)

    def finish(self):
        if self.__slot is not None:
            self.__writer.writeSlot(self.__slot)
        self.__writer.close()


def resample_impl(barFeed, frequency, csvFile):
    sampler = Sampler(barFeed, frequency, csvFile)

    # Process all bars.
    disp = dispatcher.Dispatcher()
    disp.addSubject(barFeed)
    disp.run()

    sampler.finish()


def resample_to_csv(barFeed, frequency, csvFile):
    """Resample a BarFeed into a CSV file grouping bars by a certain frequency.
    The resulting file can be loaded using :class:`pyalgotrade.barfeed.csvfeed.GenericBarFeed`.
    The CSV file will have the following format:
    ::

        Date Time,Open,High,Low,Close,Volume,Adj Close
        2013-01-01 00:00:00,13.51001,13.56,13.51,13.56,273.88014126,13.51001


    :param barFeed: The bar feed that will provide the bars. It should only hold bars from a single instrument.
    :type barFeed: :class:`pyalgotrade.barfeed.BarFeed`
    :param frequency: The grouping frequency in seconds. Must be > 0.
    :param csvFile: The path to the CSV file to write.
    :type csvFile: string.

    .. note::
        * Datetimes are stored without timezone information.
        * **Adj Close** column may be empty if the input bar feed doesn't have that info.
    """

    if frequency > 0:
        resample_impl(barFeed, frequency, csvFile)
    else:
        raise Exception("Invalid frequency")
