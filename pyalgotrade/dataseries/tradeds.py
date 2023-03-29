"""
.. moduleauthor:: Robert Lee
"""

from pyalgotrade import dataseries

import six


class TradeDataSeries(dataseries.SequenceDataSeries):
    """A DataSeries of :class:`pyalgotrade.bar.Trade` instances.

    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """

    def __init__(self, maxLen=None):
        super(TradeDataSeries, self).__init__(maxLen)
        self.__tradeIdDS = dataseries.SequenceDataSeries(maxLen)
        self.__priceDS = dataseries.SequenceDataSeries(maxLen)
        self.__sizeDS = dataseries.SequenceDataSeries(maxLen)
        self.__isBuyDS = dataseries.SequenceDataSeries(maxLen)
        self.__extraDS = {}

    def __getOrCreateExtraDS(self, name):
        ret = self.__extraDS.get(name)
        if ret is None:
            ret = dataseries.SequenceDataSeries(self.getMaxLen())
            self.__extraDS[name] = ret
        return ret

    def append(self, trade):
        self.appendWithDateTime(trade.getDateTime(), trade)

    def appendWithDateTime(self, dateTime, trade):
        assert(dateTime is not None)
        assert(trade is not None)

        super(TradeDataSeries, self).appendWithDateTime(dateTime, trade)

        self.__tradeIdDS.appendWithDateTime(dateTime, trade.getTradeId())
        self.__priceDS.appendWithDateTime(dateTime, trade.getPrice())
        self.__sizeDS.appendWithDateTime(dateTime, trade.getSize())
        self.__isBuyDS.appendWithDateTime(dateTime, trade.getIsBuy())

        # Process extra columns.
        for name, value in six.iteritems(trade.getExtraColumns()):
            extraDS = self.__getOrCreateExtraDS(name)
            extraDS.appendWithDateTime(dateTime, value)

    def getTradeIdDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the trade Ids."""
        return self.__tradeIdDs

    def getPriceDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the trade prices."""
        return self.__priceDS

    def getSizeDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the trade sizes."""
        return self.__sizeDS

    def getIsBuyDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with whether the trades are buys."""
        return self.__isBuyDS

    def getExtraDataSeries(self, name):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` for an extra column."""
        return self.__getOrCreateExtraDS(name)
