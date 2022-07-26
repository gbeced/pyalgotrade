from pyalgotrade import technical
from pyalgotrade import dataseries
class DonchianEventWindow(technical.EventWindow):

    def __init__(self, period, channel, useAdjustedValues):
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

    def getValue(self):
        return self.__value

class DonchianChannel(technical.EventBasedFilter):
    """
    Donchian Channel as described in https://www.investopedia.com/terms/d/donchianchannels.asp.

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
        opposite end. 
    """
    
    def __init__(self, barDataSeries, period, channel, useAdjustedValues=True, maxLen=None):
        super(DonchianChannel, self).__init__(barDataSeries, 
            DonchianEventWindow(period, channel, useAdjustedValues), maxLen)