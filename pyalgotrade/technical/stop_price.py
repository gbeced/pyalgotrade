from pyalgotrade import technical


class SMAEventWindow_Frac(technical.EventWindow):
    def __init__(self, fracOfEntry, period):
        assert(period > 0)
        super(SMAEventWindow_Frac, self).__init__(period)
        self.__value = None
        self.fracOfEntry = fracOfEntry

    def onNewValue(self, dateTime, value):
        firstValue = None
        if len(self.getValues()) > 0:
            firstValue = self.getValues()[0]
            assert(firstValue is not None)

        super(SMAEventWindow_Frac, self).onNewValue(dateTime, value)

        if value is not None and self.windowFull():
            if self.__value is None:
                self.__value = self.getValues().mean()
            else:
                self.__value = self.__value + value / float(self.getWindowSize()) - firstValue / float(self.getWindowSize())

    def getValue(self):
        return self.__value * self.fracOfEntry


class STOP_PRICE(technical.EventBasedFilter):
    """STOP_Price Indicator using SMA Filter.

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param fracOfEntry: Fraction of the entry price that should be used to calcualte STOP_PRICE = fracOfEntry * Price.
    :type fracOfEntry: float.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """
    def __init__(self, dataSeries, fracOfEntry, maxLen=None):
        assert fracOfEntry >= 0, "fracOfEntry must be non-negtive"
        self.fracOfEntry = fracOfEntry
        super(STOP_PRICE, self).__init__(dataSeries, SMAEventWindow_Frac(fracOfEntry, period=1), maxLen)


