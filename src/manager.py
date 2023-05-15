import time
import yaml
from logzio_shipper import *
from datetime import datetime, timedelta
from urllib.parse import urlparse


logger = logging.getLogger(__name__)

class Manager:

    def __init__(self):
        """
        Initializes a new Manager object.

        :param config_file: The path to the configuration file.
        :param last_start_dates_file: The path to the file that stores the last start dates.
        """

        self.config_file = "src/shared/config.yaml"
        self.last_start_dates_file = "src/shared/lastTime.txt"
        self.logzio_url = None
        self.logzio_token = None
        self.logzio_shipper = None
        self.jumpcloud_url = None
        self.jumpcloud_token = None
        self.jumpcloud_time_interval = None
        self.last_time_event = None
        self.headers = None

    def is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def last_time_plus_sec(self, last_time:str) -> str:
        """
        Adds one second to a given timestamp.

        :param last_time: The timestamp to add one second to.
        :return: A new timestamp with one second added.
        """
        last_time_event = last_time.replace('Z', '+00:00')
        last_time_event = datetime.fromisoformat(last_time_event)
        last_time_event = last_time_event + timedelta(seconds=1)
        last_time_event = last_time_event.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return last_time_event

    def read_config(self):
        """
        Reads configuration information from a YAML file.
        """
        with open(self.config_file) as f:
            data = yaml.safe_load(f)

        self.logzio_url = data['logzio']['url']
        self.logzio_token = data['logzio']['token']
        self.jumpcloud_url = "https://api.jumpcloud.com/insights/directory/v1/events"
        if not self.is_valid_url(self.jumpcloud_url):
            logger.error("Please enter valid url for jumpcloud API")
        self.last_time_event = data['jumpcloud_api']['start_date']
        if self.last_time_event is None:
            self.last_time_event = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

        self.jumpcloud_token = data['jumpcloud_api']['credentials']['token']
        self.jumpcloud_time_interval = data['jumpcloud_api']['settings']['time_interval']

        if self.jumpcloud_time_interval is None:
            self.jumpcloud_time_interval = 5


    def write_last_time_to_file(self,last_time_event):
        with open(self.last_start_dates_file, 'w') as f:
            f.write(last_time_event)
    def send_events_to_logzio(self, events) -> None:
        """
        Sends a list of events to Logz.io.

        :param events: The list of events to send to Logz.io.
        """
        try:
            if len(events) != 0:
                logger.info("Events number: {}".format(len(events)))
                for event in events:
                    event_str = json.dumps(event)
                    self.logzio_shipper.add_log_to_send(event_str)

                self.logzio_shipper.send_to_logzio()
                self.last_time_event = events[-1]['timestamp']
            else:
                logger.info("No events")
            self.last_time_event = self.last_time_plus_sec(self.last_time_event)
            self.write_last_time_to_file(self.last_time_event)
        except Exception as e:
           logger.error("Failed to send data to Logz.io... {}".format(e))


    def run(self):

        self.read_config()
        self.headers = {
            "accept": "application/json",
            "x-api-key": self.jumpcloud_token,
            "content-type": "application/json"
        }

        self.logzio_shipper = LogzioShipper(self.logzio_url, self.logzio_token)
        while True:
            body = {
                "service": ["all"],
                "start_time": self.last_time_event,
            }
            logger.info("Requesting events from jumpcloud")
            try:
                response = requests.request("POST", self.jumpcloud_url, json=body, headers=self.headers)
                if response.status_code == 200:
                    events = json.loads(response.content.decode('utf-8'))
                    try:
                        self.send_events_to_logzio(events)
                    except Exception as e:
                        logger.error("Failed to send events to Logz.io... {}".format(e))
                else:
                    logger.error("Failed to retrieve events from JumpCloud API. Response status code: {}".format(
                        response.status_code))
            except requests.exceptions.HTTPError as errh:
                if (response.status_code == 401):
                    logger.error("HTTP Error: 401 Unauthorized (Invalid API Key)")
                elif (response.status_code == 402):
                    logger.error("HTTP Error: 402 Directory Insights is not enabled for your organization")
                else:
                    logger.error(f"HTTP Error: {errh}")
            except requests.exceptions.ConnectionError as errc:
                logger.error(f"Error Connecting: {errc}")
            except requests.exceptions.Timeout as errt:
                logger.error(f"Timeout Error: {errt}")
            except requests.exceptions.RequestException as err:
                logger.error(f"Something went wrong: {err}")

            logger.info("Going to sleep for {}m".format(self.jumpcloud_time_interval))
            time.sleep(self.jumpcloud_time_interval * 60)
        else:
                logger.info(response.text)