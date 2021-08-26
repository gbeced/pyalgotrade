from pyalgotrade import technical


class SMAEventWindow_Frac(technical.EventWindow):
    def __init__(self, percent_change, period):
        assert(period > 0)
        super(SMAEventWindow_Frac, self).__init__(period)
        self.__value = None
        self.percent_change = percent_change

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
        return self.__value * (self.percent_change + 100) / 100


class STOP_PRICE(technical.EventBasedFilter):
    """STOP_Price Indicator using SMA Filter.

    :param dataSeries: The DataSeries instance being filtered.
    :type dataSeries: :class:`pyalgotrade.dataseries.DataSeries`.
    :param percent_change: Percent Change in entry price used to calculate STOP_PRICE = (percent_change + 100 ) / 100 * Price.
    :type percent_change: float.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """
    def __init__(self, dataSeries, percent_change, maxLen=None):
        assert percent_change >= -100, "percent_change must be greater than -100"
        self.percent_change = percent_change
        super(STOP_PRICE, self).__init__(dataSeries, SMAEventWindow_Frac(percent_change, period=1), maxLen)




