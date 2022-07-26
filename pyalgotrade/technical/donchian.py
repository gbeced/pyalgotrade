from pyalgotrade import technical
from pyalgotrade import dataseries
from pyalgotrade.dataseries import bards
from .highlow import High, Low, HighLowEventWindow
from pyalgotrade.technical import price


class DonchianEventWindow(technical.EventWindow):

    def __init__(self, period, channel, useAdjustedValues):
        # period += 1
        assert(period > 1)
        super(DonchianEventWindow, self).__init__(period)
        self.__channel = channel
        self.__useAdjustedValues = useAdjustedValues
        self.__upperChannel = dataseries.SequenceDataSeries(period)
        self.__lowerChannel = dataseries.SequenceDataSeries(period)

    def onNewValue(self, dateTime, value):
        self.__value = None
        self.__upperChannel.append(value.getHigh(self.__useAdjustedValues))
        self.__lowerChannel.append(value.getLow(self.__useAdjustedValues))

        if self.__channel == "upper":
            _value = max(self.__upperChannel)
        elif self.__channel == "lower":
            _value = min(self.__lowerChannel)
        elif self.__channel == "middle":
            _value = (max(self.__upperChannel) + min(self.__lowerChannel)) / 2
        elif self.__channel == "channelRange":
            _value = max(self.__upperChannel) - min(self.__lowerChannel)
        else:
            raise ValueError(f"Channel type {self.channel} is not available." +
                    " Choices are 'upper', 'middle', or 'lower'.")

        if _value is not None and self.windowFull():
            self.__value = self.getValues()[-1]

        super(DonchianEventWindow, self).onNewValue(dateTime, _value)

        # if _value is not None and self.windowFull():
        #     self.__value = self.getValues()[1:][-2]

    def getValue(self):
        return self.__value

class DonchianChannel(technical.EventBasedFilter):
    """
    
    """
    
    def __init__(self, barDataSeries, period, channel, useAdjustedValues=True, maxLen=None):
        super(DonchianChannel, self).__init__(barDataSeries, 
            DonchianEventWindow(period, channel, useAdjustedValues), maxLen)

class _DonchianChannel(HighLowEventWindow):
    """Donchian Channel as described in https://www.investopedia.com/terms/d/donchianchannels.asp.

    Donchian Channels calculates the high and low to create an envelope around a
    price series. Signals are generated when the price moves outside the 
    channels.

    :param barDataSeries: The BarDataSeries instance being filtered.
    :type barDataSeries: :class:`pyalgotrade.dataseries.bards.BarDataSeries`.
    :param upperChannelPeriod: Number of periods used to calculate the upper channel SMA.
    :type upperChannelPeriod: int.
    :param lowerChannelPeriod: Number of periods used to calculate the lower channel SMA.
    :type lowerChannelPeriod: int.
    :param maxLen: The maximum number of values to hold.
        Once a bounded length is full, when new items are added, a corresponding number of items are discarded from the
        opposite end. If None then dataseries.DEFAULT_MAX_LEN is used.
    :type maxLen: int.
    """
    def __init__(self, barDataSeries, period=50, channel="middle", maxLen=None):
        if not isinstance(barDataSeries, bards.BarDataSeries):
            raise Exception("barDataSeries must be a dataseries.bards.BarDataSeries instance")
        
        self.channel = channel
        self.__middleChannel = dataseries.SequenceDataSeries(maxLen)
        self.__upperChannel = dataseries.SequenceDataSeries(maxLen)
        self.__lowerChannel = dataseries.SequenceDataSeries(maxLen)
        self.upper = price.PRICE_WINDOW(barDataSeries, period=period, max_or_min="max", 
            price_type="High", maxLen=None)
        self.lower = price.PRICE_WINDOW(barDataSeries, period=period, max_or_min="min",
            price_type="Low", maxLen=None)
        # self.__upperChannel = High(barDataSeries.getAdjHighDataSeries(), 
        #     period=period, maxLen=maxLen)
        # self.__lowerChannel = Low(barDataSeries.getAdjLowDataSeries(), 
        #     period=period, maxLen=maxLen)
        self.upperValue = None
        self.lowerValue = None
        self.middleValue = None 
        # dataSeries.getNewValueEvent().subscribe(self.__onNewValue)

    def __onNewValue(self, dataSeries, dateTime, value):
        self.middleValue = None

        if value is not None:
            self.upper = self.__upperChannel[-2]
            self.lower = self.__lowerChannel[-2]
            if self.upper is not None and self.lower is not None:
                self.middleValue = (self.upper + self.lower) / 2

        self.__middleChannel.appendWithDateTime(dateTime, self.middleValue)
        self.__upperChannel.appendWithDateTime(dateTime, self.upperValue)
        self.__lowerChannel.appendWithDateTime(dateTime, self.lowerValue)

    def getUpperChannel(self):
        """
        Returns the upper channel as a :class:`pyalgotrade.dataseries.DataSeries`.
        """
        return self.__upperChannel

    def getMiddleChannel(self):
        """
        Returns the middle channel as a :class:`pyalgotrade.dataseries.DataSeries`.
        """
        return self.__middleChannel

    def getLowerChannel(self):
        """
        Returns the lower channel as a :class:`pyalgotrade.dataseries.DataSeries`.
        """
        return self.__lowerChannel

    def getValue(self): 
        """
        Return latest value of chosen channel
        """
        if self.channel == "upper":
            return self.upperValue
        elif self.channel == "middle":
            return (self.upperValue + self.lowerValue) / 2
        elif self.channel == "lower":
            return self.lowerValue
        elif self.channel == "channelRange":
            return self.upperValue - self.lowerValue
        else:
            raise ValueError(f"Channel type {self.channel} is not available." +
                    " Choices are 'upper', 'middle', or 'lower'.")