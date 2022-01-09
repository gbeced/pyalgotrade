"""
.. moduleauthor:: Robert Lee
"""

from pyalgotrade import dataseries

import six


class QuoteDataSeries(dataseries.SequenceDataSeries):
    """A DataSeries of :class:`pyalgotrade.bar.Quote` instances.

    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """

    def __init__(self, maxLen=None):
        super(QuoteDataSeries, self).__init__(maxLen)
        self.__askExchangeDS = dataseries.SequenceDataSeries(maxLen)
        self.__askPriceDS = dataseries.SequenceDataSeries(maxLen)
        self.__askSizeDS = dataseries.SequenceDataSeries(maxLen)
        self.__bidExchangeDS = dataseries.SequenceDataSeries(maxLen)
        self.__bidPriceDS = dataseries.SequenceDataSeries(maxLen)
        self.__bidSizeDS = dataseries.SequenceDataSeries(maxLen)
        self.__quoteConditionDS = dataseries.SequenceDataSeries(maxLen)
        self.__tapeDS = dataseries.SequenceDataSeries(maxLen)
        self.__extraDS = {}

    def __getOrCreateExtraDS(self, name):
        ret = self.__extraDS.get(name)
        if ret is None:
            ret = dataseries.SequenceDataSeries(self.getMaxLen())
            self.__extraDS[name] = ret
        return ret

    def append(self, trade):
        self.appendWithDateTime(trade.getDateTime(), trade)

    def appendWithDateTime(self, dateTime, quote):
        assert(dateTime is not None)
        assert(quote is not None)

        super(QuoteDataSeries, self).appendWithDateTime(dateTime, quote)

        self.__askExchangeDS.appendWithDateTime(dateTime, quote.getAskExchange())
        self.__askPriceDS.appendWithDateTime(dateTime, quote.getAskPrice())
        self.__askSizeDS.appendWithDateTime(dateTime, quote.getAskSize())
        self.__bidExchangeDS.appendWithDateTime(dateTime, quote.getBidExchange())
        self.__bidPriceDS.appendWithDateTime(dateTime, quote.getBidPrice())
        self.__bidSizeDS.appendWithDateTime(dateTime, quote.getBidSize())
        self.__quoteConditionDS.appendWithDateTime(dateTime, quote.getQuoteCondition())
        self.__tapeDS.appendWithDateTime(dateTime, quote.getTape())

        # Process extra columns.
        for name, value in six.iteritems(quote.getExtraColumns()):
            extraDS = self.__getOrCreateExtraDS(name)
            extraDS.appendWithDateTime(dateTime, value)

    def getAskExchangeDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the ask exchanges."""
        return self.__askExchangeDS

    def getAskPriceDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the ask prices."""
        return self.__askPriceDS

    def getAskSizeDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the ask sizes."""
        return self.__askSizeDS

    def getBidExchangeDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the bid exchanges."""
        return self.__bidExchangeDS

    def getBidPriceDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the bid prices."""
        return self.__bidPriceDS

    def getBidSizeDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the bid sizes."""
        return self.__bidSizeDS

    def getQuoteConditionDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the quote conditions."""
        return self.__quoteConditionDS
    
    def getTapeDataSeries(self):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` with the quote tapes."""
        return self.__tapeDS

    def getExtraDataSeries(self, name):
        """Returns a :class:`pyalgotrade.dataseries.DataSeries` for an extra column."""
        return self.__getOrCreateExtraDS(name)