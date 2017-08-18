import json
import time
import tweepy
from datetime import datetime
from tweepy.streaming import StreamListener
from constants import *
from settings import *


class TwitterBot(StreamListener):
    """
    Basic bot to retweet specific user's tweets
    """

    def __init__(self):
        """
        Instantiate a new bot
        """
        super().__init__()

        # Will only reply to every 3rd or so tweet, defined in settings
        self.received_tweet_count = 0

        # Twitter api init
        self.auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        self.auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
        self.twitter_api = tweepy.API(self.auth)

        print('Authenticated, creating stream...')

        self._init_stream()

    def on_data(self, _data):
        """
        Raw data received from the twitter stream.
        Populate queue dependent on operating mode, logic lives here

        :param _data: raw twitter output, json string of data
         :type _data: str
        """
        # There are times where the twitter stream fails and will send a NoneType object
        if not _data:
            print('**************************************************')
            print('**** Stream error, received empty data object ****')
            print('**************************************************')
            return

        data = json.loads(_data)

        # Only follow the created at tweets, ignoring replies, etc when trolling
        if CREATED_AT in data:
            if data[USER][ID_STRING] not in self.trolling_ids:
                return

            # Only troll raw tweets, not replies
            if data[REPLY_TO_STATUS_ID]:
                return

            print('New tweet, current count:', self.received_tweet_count)

            # If received enough than retweet it
            if self.received_tweet_count == TWEET_INTERVAL:
                raw_tweet_url = TWITTER_URL + data[USER][SCREEN_NAME] + STATUS_PATH + data[ID_STRING]
                print(
                    '\n== New Tweet Received @', datetime.now(),
                    'Tweet URL:',  raw_tweet_url, '=='
                )

                time.sleep(RETWEET_WAIT_PERIOD)
                self.twitter_api.retweet(data[ID])

                print('\n== Successfully retweeted! ==')

                self.received_tweet_count = 0

            else:
                self.received_tweet_count += 1

    def on_error(self, status):
        print('Error:', status)

    def _init_stream(self):
        """ Create the twitter stream """
        stream = tweepy.Stream(self.auth, self)

        try:
            print('Trying to create stream...')
            # Cannot follow based on screen name, get ids
            self.trolling_ids = [
                str(self.twitter_api.get_user(screen_name=screen_name).id)
                for screen_name in SCREEN_NAMES_TO_FOLLOW
            ]

            stream.filter(follow=self.trolling_ids)

        except Exception as e:
            print('*****************************************************')
            print('**** Stream error, init_stream.  Trying again... ****')
            print('*****************************************************')
            print(e)

            # Try again to create the stream
            time.sleep(30)
            self._init_stream()

if __name__ == '__main__':
    TwitterBot()
