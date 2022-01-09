"""
.. moduleauthor:: Robert Lee
"""

from pyalgotrade import bar

Frequency = bar.Frequency

class Quote(object):
    # Optimization to reduce memory footprint.
    __slots__ = (
        '__dateTime',
        '__ask_exchange',
        '__ask_price',
        '__ask_size',
        '__bid_exchange',
        '__bid_price',
        '__bid_size',
        '__quote_condition',
        '__tape',
        '__extra'
        )

    def __init__(self, dateTime,
        askExchange, askPrice, askSize,
        bidExchange, bidPrice, bidSize,
        quoteCondition, tape, extra = {}):

        self.__dateTime = dateTime
        self.__askExchange = askExchange
        self.__askPrice = askPrice
        self.__askSize = askSize
        self.__bidExchange = bidExchange
        self.__bidPrice = bidPrice
        self.__bidSize = bidSize
        self.__quoteCondition = quoteCondition
        self.__tape = tape
        self.__extra = extra

    def __setstate__(self, state):
        (self.__dateTime,
            self.__askExchange,
            self.__askPrice,
            self.__askSize,
            self.__bidExchange,
            self.__bidPrice,
            self.__bidSize,
            self.__quoteCondition,
            self.__tape,
            self.__extra
            ) = state

    def __getstate__(self):
        return (
            self.__dateTime,
            self.__askExchange,
            self.__askPrice,
            self.__askSize,
            self.__bidExchange,
            self.__bidPrice,
            self.__bidSize,
            self.__quoteCondition,
            self.__tape,
            self.__extra
        )

    def getFrequency(self):
        return Frequency.QUOTE

    def getDateTime(self):
        return self.__dateTime

    def getAskExchange(self):
        return self.__askExchange

    def getAskPrice(self):
        return self.__askPrice
    
    def getAskSize(self):
        return self.__askSize
    
    def getBidExchange(self):
        return self.__bidExchange
    
    def getBidPrice(self):
        return self.__bidPrice
    
    def getBidSize(self):
        return self.__bidSize
    
    def getQuoteCondition(self):
        return self.__quoteCondition
    
    def getTape(self):
        return self.__tape
    
    def getExtraColumns(self):
        return self.__extra

class Quotes(object):

    """A group of :class:`Quote` objects.

    :param quoteDict: A map of instrument to :class:`Quote` objects.
    :type quoteDict: map.

    .. note::
        All bars must have the same datetime.
    """

    def __init__(self, quoteDict):
        if len(quoteDict) == 0:
            raise Exception("No quotes supplied")

        # Check that bar datetimes are in sync
        firstDateTime = None
        firstInstrument = None
        for instrument, currentQuote in six.iteritems(quoteDict):
            if firstDateTime is None:
                firstDateTime = currentQuote.getDateTime()
                firstInstrument = instrument
            elif currentQuote.getDateTime() != firstDateTime:
                raise Exception("Quote data times are not in sync. %s %s != %s %s" % (
                    instrument,
                    currentQuote.getDateTime(),
                    firstInstrument,
                    firstDateTime
                ))

        self.__quoteDict = quoteDict
        self.__dateTime = firstDateTime

    def __getitem__(self, instrument):
        """Returns the :class:`pyalgoquote.bar.Quote` for the given instrument.
        If the instrument is not found an exception is raised."""
        return self.__quoteDict[instrument]

    def __contains__(self, instrument):
        """Returns True if a :class:`pyalgoquote.bar.Quote` for the given instrument is available."""
        return instrument in self.__quoteDict

    def items(self):
        return list(self.__quoteDict.items())

    def keys(self):
        return list(self.__quoteDict.keys())

    def getInstruments(self):
        """Returns the instrument symbols."""
        return list(self.__quoteDict.keys())

    def getDateTime(self):
        """Returns the :class:`datetime.datetime` for this set of quotes."""
        return self.__dateTime

    def getQuote(self, instrument):
        """Returns the :class:`pyalgoquote.bar.Quote` for the given instrument or None if the instrument is not found."""
        return self.__quoteDict.get(instrument, None)