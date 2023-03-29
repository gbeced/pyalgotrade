"""
An intentionally simplistic order book implementation
"""

import time

from enum import Enum
from collections import namedtuple
from sortedcontainers import SortedDict


class Side(Enum):
    Bid = 1
    bid = 1
    Ask = 2
    ask = 2

Bid, Ask = Side.Bid, Side.Ask

# These classes are used to update the OrderBook

AbstractMarketDataWrapper = namedtuple('AbstractMarketDataWrapper', 'ts venue symbol data')
AbstractMarketDataWrapper.__new__.__defaults__ = (0, '', '', [])

class MarketUpdate(AbstractMarketDataWrapper):
    """An incremental change to the order book"""
    pass
class MarketSnapshot(AbstractMarketDataWrapper):
    """A new full order book definition"""
    # unenforced, but data should only contain Assigns
    pass

# Market{Update,Snapshot} are really just wrappers for these (within .data)
AbstractMarketDataDelta = namedtuple('AbstractMarketDataDelta', 'rts venue symbol price size side')
AbstractMarketDataDelta.__new__.__defaults__ = (0, '', '', 0, 0, Ask)

class Assign(AbstractMarketDataDelta):
    """Set a price/size/side"""
    pass
class Increase(AbstractMarketDataDelta):
    """Increase the price/side/size by size"""
    pass
class Decrease(AbstractMarketDataDelta):
    """Decrease the price/side/size by size"""
    pass

PriceLevel = Assign

# helper object to add some structure

Inside = namedtuple('Inside', 'bid ask')

# The actual OrderBook object

class OrderBook():
    """
    Generic book; understands only common messages (for updating the book)
    Note: prices and sizes are Decimals (already decoded). Implements L1/L2.
    """
    def __init__(self, venue=None, symbol=None):
        self.venue   = venue
        self.symbol  = symbol
        self.reset()

    def reset(self):
        """Reset the OrderBook to an empty state"""
        self.bids   = SortedDict(lambda k:-k, {})   # maps price: PriceLevel(size, tick)
        self.asks   = SortedDict({})   # maps price: PriceLevel(size, tick)
        self.last   = None # the last MarketUpdate or MarketSnapshot

    def is_empty(self):
        """returns True iff the OrderBook is empty"""
        return self.last is None
        #return not (self.bids and self.asks)

    def update(self, update):
        """Update the OrderBook with the given update
        (either a MarketSnapshot or a MarketUpdate)
        """

        def set_pricelevel(side, assign):
            ap = assign.price
            if assign.size > 0: side[ap] = assign
            elif ap in side: del side[ap]
        s_pl = set_pricelevel

        def make_assign(update, **kwargs):
            assign = update._asdict()
            assign.update(kwargs)
            return PriceLevel(**assign)
        mk_a = make_assign

        g_sz = lambda s, p: s.get(p, PriceLevel()).size

        # check type(update) == MarketUpdate ?
        if type(update) == MarketSnapshot: self.reset()
        for t in update.data:
            tt = type(t)
            s = { Ask: self.asks, Bid: self.bids }.get(t.side, None)
            if s is None: raise ValueError("Unknown side: %r" % t.side)
            tp, ts = t.price, t.size
            if   tt == Assign:   s_pl(s, t)
            elif tt == Increase: s_pl(s, mk_a(t, size=g_sz(s, tp) + ts))
            elif tt == Decrease: s_pl(s, mk_a(t, size=g_sz(s, tp) - ts))
            else: raise ValueError("Unknown type %r of %r" % (type(t), t))

        self.last = update
        return self

    def get_marketsnapshot(self):
        """Return the OrderBook as a MarketSnapshot"""
        data = self.bids.values() + self.asks.values()
        return MarketSnapshot(time.time(), self.venue, self.symbol, data)

    @classmethod
    def from_snapshot(cls, snapshot):
        """Create the OrderBook from a MarketSnapshot"""
        return cls(snapshot.venue, snapshot.symbol).update(snapshot)

    @property
    def inside(self):
        """Return the closest bid and ask PriceLevels"""
        return Inside(self.inside_bid(), self.inside_ask())

    @property
    def inside_bid(self):
        """Return the highest bid PriceLevel"""
        try:
            return self.bids[self.bids.iloc[0]]
        except IndexError:
            print("!!! Book for venue %s:%s bids are empty!!"%(self.venue, self.symbol))
            raise

    @property
    def inside_ask(self):
        """Return the lowest ask PriceLevel"""
        try:
            return self.asks[self.asks.iloc[0]]
        except IndexError:
            print("!!! Book for venue %s:%s asks are empty!!"%(self.venue, self.symbol))
            raise

    def nvolume(self, nlevels=None):
        """ return the inside <nlevels> levels on each side of the book
              nlevels = None (the default) means 'all'
        """
        bids = self.bids.values()[:nlevels]
        asks = self.asks.values()[:nlevels]
        return { 'bids': list(bids), 'asks': list(asks) }

    def price_for_size(self, side, size):
        """
        The cost of the specifed size on the specified side.
        Note that this is not 'to fill an order on the specified side',
        because Asks fill Bid orders and vice versa.
        """
        pside = { Bid: self.bids, Ask: self.asks }[side]
        sizeleft = size
        value = 0
        for price in pside:
            pl = pside[price]
            s = min(sizeleft, pl.size)
            value += s * price
            sizeleft -= s
            if not sizeleft: break
        return value

    def npfs(self, size):
        """
        Normalized Price For Size
        """
        return self.price_for_size(Bid, size)/self.price_for_size(Ask, size)

    def size_for_price(self, side, price):
        """
        How much size the specified price is worth on the specified side.
        """
        pside = { Bid: self.bids, Ask: self.asks }[side]
        priceleft = price
        size = 0
        for price in pside:
            pl = pside[price]
            p = price * pl.size
            if p > priceleft:
                priceleft -= p
                size += pl.size
            else:
                size += priceleft / price
                break
        return size

    def nsfp(self, price):
        """Normalized Size For Price"""
        return self.size_for_price(Bid, price)/self.size_for_price(Ask, price)
