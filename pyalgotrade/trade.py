"""
.. moduleauthor:: Robert Lee
"""

from pyalgotrade import bar

Frequency = bar.Frequency

class Trade(object):

    # Optimization to reduce memory footprint.
    __slots__ = ('__dateTime', '__tradeId', '__price', '__size', '__isBuy')

    def __init__(self, dateTime, tradeId, price, size, isBuy, extra = {}):
        self.__dateTime = dateTime
        self.__tradeId = tradeId
        self.__price = price
        self.__size = size
        self.__isBuy = isBuy
        self.__extra = extra

    def __setstate__(self, state):
        (self.__dateTime, self.__tradeId, self.__price, self.__amount, self.__extra) = state

    def __getstate__(self):
        return (self.__dateTime, self.__tradeId, self.__price, self.__amount, self.__extra)

    def getFrequency(self):
        return Frequency.TRADE
    
    def getDateTime(self):
        return self.__dateTime
        
    def getTradeId(self):
        return self.__tradeId

    def getPrice(self):
        return self.__price

    def getSize(self):
        return self.__size

    def getIsBuy(self):
        return self.__isBuy
    
    def getExtraColumns(self):
        return self.__extra

class Trades(object):

    """A group of :class:`Trade` objects.

    :param tradeDict: A map of instrument to :class:`Trade` objects.
    :type tradeDict: map.

    .. note::
        All bars must have the same datetime.
    """

    def __init__(self, tradeDict):
        if len(tradeDict) == 0:
            raise Exception("No trades supplied")

        # Check that bar datetimes are in sync
        firstDateTime = None
        firstInstrument = None
        for instrument, currentTrade in six.iteritems(tradeDict):
            if firstDateTime is None:
                firstDateTime = currentTrade.getDateTime()
                firstInstrument = instrument
            elif currentTrade.getDateTime() != firstDateTime:
                raise Exception("Trade data times are not in sync. %s %s != %s %s" % (
                    instrument,
                    currentTrade.getDateTime(),
                    firstInstrument,
                    firstDateTime
                ))

        self.__tradeDict = tradeDict
        self.__dateTime = firstDateTime

    def __getitem__(self, instrument):
        """Returns the :class:`pyalgotrade.bar.Trade` for the given instrument.
        If the instrument is not found an exception is raised."""
        return self.__tradeDict[instrument]

    def __contains__(self, instrument):
        """Returns True if a :class:`pyalgotrade.bar.Trade` for the given instrument is available."""
        return instrument in self.__tradeDict

    def items(self):
        return list(self.__tradeDict.items())

    def keys(self):
        return list(self.__tradeDict.keys())

    def getInstruments(self):
        """Returns the instrument symbols."""
        return list(self.__tradeDict.keys())

    def getDateTime(self):
        """Returns the :class:`datetime.datetime` for this set of trades."""
        return self.__dateTime

    def getTrade(self, instrument):
        """Returns the :class:`pyalgotrade.bar.Trade` for the given instrument or None if the instrument is not found."""
        return self.__tradeDict.get(instrument, None)
