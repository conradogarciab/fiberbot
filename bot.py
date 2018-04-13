import os
import sys
import twitter
import pyspeedtest
import logging
from time import sleep
from bitmath import Byte

DEFAULT_MESSAGE = 'Tengo contratado {0} y mi velocidad de descarga es de {1}, @CableFibertel'


class SpeedBot():
    def __init__(self,
                 consumer_key, consumer_secret, access_key,
                 access_secret, expected_speed, retry_time,
                 limit=None):
        self.api = twitter.Api(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token_key=access_key,
            access_token_secret=access_secret,
        )
        self.speedtest = pyspeedtest.SpeedTest()
        logging.basicConfig(
            format='%(asctime)s %(message)s',
            datefmt='%d/%m/%Y %I:%M:%S %p',
            level=logging.INFO
        )
        self.message = DEFAULT_MESSAGE
        self.expected_speed = expected_speed
        self.limit = limit or expected_speed / 2

        logging.info("""Starting bot with
            FIBERBOT_CONSUMER_KEY {}
            FIBERBOT_CONSUMER_SECRET {}
            FIBERBOT_ACCESS_TOKEN_KEY {}
            FIBERBOT_ACCESS_TOKEN_SECRET {}
            FIBERBOT_EXPECTED_SPEED {}
        """.format(consumer_key, consumer_secret, access_key, access_secret,
                   expected_speed))

        test_message = self.message.format('EXPECTED_SPEED', 'DOWNLOAD_SPEED')

        logging.info('Message will be \"{}\"'.format(test_message))

        logging.info("""Tweet will go out every {} seconds only if download speed is lower than {}""".format(retry_time, limit))

    def download_speed(self):
        logging.info('Starting to measure download speed')
        return self.speedtest.download()

    def upload_speed(self):
        logging.info('Starting to measure upload speed')
        return self.speedtest.upload()

    def ping(self):
        logging.info('Starting to measure ping')
        return self.speedtest.ping()

    def post(self, message=''):
        if (len(message) < 140):
            logging.info('Tweeting "{}"'.format(message))
            try:
                self.api.PostUpdate(message)
            except Exception as e:
                logging.error('Could not tweet, {}'.format(e))
        else:
            logging.info(
                    'Couldn\'t tweet "{}"... is too long'.format(message[:20]))

    def format_tweet(self, download, upload, ping):
        message = self.message.format(self.expected_speed, download)
        return message

    def format_speed(self, speed):
        return Byte(speed).best_prefix().format("{value:.2f} {unit}")

    def start(self):
        download_speed = self.download_speed()
        formatted_download_speed = self.format_speed(download_speed)
        if (download_speed < self.limit):
            formatted_upload_speed = self.format_speed(self.upload_speed())
            ping = self.ping()
            self.post(
                self.format_tweet(formatted_download_speed,
                                  formatted_upload_speed,
                                  ping))
        else:
            logging.info('Speed is {}, not twitting'.format(
                formatted_download_speed
            ))

if __name__ == '__main__':
    retry_time = os.environ.get('FIBERBOT_RETRY_TIME', 1000)
    bot = SpeedBot(
        consumer_key=os.environ.get('FIBERBOT_CONSUMER_KEY'),
        consumer_secret=os.environ.get('FIBERBOT_CONSUMER_SECRET'),
        access_key=os.environ.get('FIBERBOT_ACCESS_TOKEN_KEY'),
        access_secret=os.environ.get('FIBERBOT_ACCESS_TOKEN_SECRET'),
        expected_speed=os.environ.get('FIBERBOT_EXPECTED_SPEED', 25),
        limit=os.environ.get('FIBERBOT_SPEED_LIMIT'),
        retry_time=retry_time
    )
    while True:
        try:
            bot.start()
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            logging.error("""Something went wrong, {0} re trying in {1} seconds""".format(e, retry_time))
        sleep(retry_time)
