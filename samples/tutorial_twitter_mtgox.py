from pyalgotrade import strategy
from pyalgotrade.mtgox import client
from pyalgotrade.mtgox import barfeed
from pyalgotrade.mtgox import broker
from pyalgotrade.twitter import feed as twitterfeed

import datetime

class Strategy(strategy.BaseStrategy):
    def __init__(self, instrument, feed, brk, mtgoxClient, twitterFeed):
        strategy.BaseStrategy.__init__(self, feed, brk)
        self.__instrument = instrument

        # Subscribe to Twitter events.
        twitterFeed.subscribe(self.onTweet)

        # It is VERY important to add the these to the event dispatch loop before running the strategy.
        self.getDispatcher().addSubject(mtgoxClient)
        self.getDispatcher().addSubject(twitterFeed)

    def onTweet(self, data):
        # Refer to https://dev.twitter.com/docs/streaming-apis/messages#Public_stream_messages for
        # the information available in data.
        try:
            print datetime.datetime.now(), "Twitter:", data["text"]
        except KeyError:
            pass

    def onBars(self, bars):
        print bars.getDateTime(), "Price:", bars[self.__instrument].getClose(), "Volume:", bars[self.__instrument].getVolume()

def main():
    # Go to http://dev.twitter.com and create an app.
    # The consumer key and secret will be generated for you after that.
    consumer_key="<YOUR-CONSUMER-KEY-HERE>"
    consumer_secret="<YOUR-CONSUMER-SECRET-HERE>"

    # After the step above, you will be redirected to your app's page.
    # Create an access token under the the "Your access token" section
    access_token="<YOUR-ACCESS-TOKEN-HERE>"
    access_token_secret="<YOUR-ACCESS-TOKEN-SECRET-HERE>"

    # Create a twitter feed to track BitCoin related events.
    track = ["bitcoin", "btc", "mtgox"]
    follow = []
    languages = ["en"]
    twitterFeed = twitterfeed.TwitterFeed(consumer_key, consumer_secret, access_token, access_token_secret, track, follow, languages)

    # Create a client responsible for all the interaction with MtGox
    mtgoxClient = client.Client("USD", None, None)
    mtgoxClient.setEnableReconnection(False)

    # Create a real-time feed that will build bars from live trades.
    feed = barfeed.LiveTradeFeed(mtgoxClient)

    # Create a backtesting broker.
    brk = broker.BacktestingBroker(200, feed)

    # Run the strategy with the feed and the broker.
    strat = Strategy("BTC", feed, brk, mtgoxClient, twitterFeed)
    strat.run()

if __name__ == "__main__":
    main()
