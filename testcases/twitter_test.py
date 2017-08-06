# PyAlgoTrade
#
# Copyright 2011-2015 Gabriel Martin Becedillas Ruiz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. moduleauthor:: Gabriel Martin Becedillas Ruiz <gabriel.becedillas@gmail.com>
"""

import os
import datetime

from . import common
try:
    # This will get environment variables set.
    import credentials
except:
    pass

from pyalgotrade import dispatcher
from pyalgotrade.twitter import feed as twitterfeed


class TwitterFeedTestCase(common.TestCase):
    def testTwitterFeed(self):
        events = {
            "on_tweet": False,
            "start": datetime.datetime.now()
        }
        disp = dispatcher.Dispatcher()

        def on_tweet(data):
            events["on_tweet"] = True
            disp.stop()

        def on_idle():
            # Stop after 5 minutes.
            if (datetime.datetime.now() - events["start"]).seconds > 60*5:
                disp.stop()

        # Create a twitter feed to track BitCoin related events.
        consumer_key = os.getenv("TWITTER_CONSUMER_KEY")
        consumer_secret = os.getenv("TWITTER_CONSUMER_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        track = ["bitcoin", "btc"]
        follow = []
        languages = ["en"]
        twitterFeed = twitterfeed.TwitterFeed(
            consumer_key,
            consumer_secret,
            access_token,
            access_token_secret,
            track,
            follow,
            languages
        )

        disp.addSubject(twitterFeed)
        twitterFeed.subscribe(on_tweet)
        disp.getIdleEvent().subscribe(on_idle)
        disp.run()

        # Check that we received both events.
        self.assertTrue(events["on_tweet"])
