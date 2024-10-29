import time
import yaml
import signal
from logzio_shipper import *
from datetime import datetime, timedelta
from urllib.parse import urlparse
import urllib
import os


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
        self.jumpcloud_org_id = None
        self.jumpcloud_time_interval = None
        self.last_time_event = None
        self.headers = None

    def handle_sigint(self, signal, frame):
        logger.info("\nCtrl+C pressed. Stopping the shipper...")
        exit(0)

    def changesValueToJSON(self, changes_list):
        json_data = {}

        for item in changes_list:
            field_name = item["field"]
            if "to" in item:
                field_value = item["to"]
                json_data[field_name + "_changed_to"] = field_value
            if "from" in item:
                field_value = item["from"]
                json_data[field_name + "_was"] = field_value
            if "to" not in item and "from" not in item:
                json_data[field_name] = None

        json_output = json.dumps(json_data)
        return json_output

    def is_valid_format(self, date_string):
        format = '%Y-%m-%dT%H:%M:%S.%fZ'
        try:
            datetime.strptime(date_string, format)
            return True
        except ValueError:
            return False

    def check_keys(self, data):
        if data is not None:
            if 'logzio' in data:
                if data['logzio'] is None:
                    logger.error("The 'logzio' dictionary is None.")
                    return False
                elif 'url' not in data['logzio'] or ('token' not in data['logzio'] and "LOGZIO_API_TOKEN" not in os.environ):  # check the configuration or the environment variable
                    logger.error("Either 'url' or 'token' is missing from the 'logzio' dictionary.")
                    return False

            else:
                logger.error("The key 'logzio' does not exist in the data dictionary.")
                return False
            if 'jumpcloud_api' in data:
                if data['jumpcloud_api'] is None:
                    logger.error("The 'jumpcloud_api' dictionary is None.")
                    return False
                if 'credentials' in data['jumpcloud_api']:
                    if data['jumpcloud_api']['credentials'] is None:
                        logger.error("The 'credentials' dictionary in 'jumpcloud_api' is None.")
                        return False
                    elif ('token' not in data['jumpcloud_api']['credentials'] and "JUMPCLOUD_API_TOKEN" not in os.environ):  # check the configuration or the environment variable
                        logger.error("The key 'token' is missing from the 'credentials' dictionary.")
                        return False
                else:
                    logger.error("The key 'credentials' does not exist in the 'jumpcloud_api' dictionary.")
                    return False

                if 'settings' in data['jumpcloud_api']:
                    if data['jumpcloud_api']['settings'] is None:
                        logger.error("The 'settings' dictionary in 'jumpcloud_api' is None.")
                        return False
                else:
                    logger.error("The key 'settings' does not exist in the 'jumpcloud_api' dictionary.")
                    return False
            else:
                logger.error("The key 'jumpcloud_api' does not exist in the data dictionary.")
                return False
        else:
            logger.error("No data could be loaded.")
            return False
        return True

    def last_time_plus_sec(self, last_time: str) -> str:
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

        if not self.check_keys(data):
            return False

        self.logzio_url = data['logzio']['url']
        self.logzio_token = os.getenv("LOGZIO_API_TOKEN") if "LOGZIO_API_TOKEN" in os.environ else data['logzio'][
            'token']
        self.jumpcloud_url = "https://api.jumpcloud.com/insights/directory/v1/events"

        # Corrected logic for start_date
        self.last_time_event = data['jumpcloud_api'].get('start_date')
        if self.last_time_event is None:
            self.last_time_event = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        elif not self.is_valid_format(self.last_time_event):
            logger.error("Invalid start_date format. Expected format is '%Y-%m-%dT%H:%M:%S.%fZ'")
            return False
        else:
            logger.info(f"Using start_date from configuration: {self.last_time_event}")

        self.jumpcloud_token = os.getenv("JUMPCLOUD_API_TOKEN") if "JUMPCLOUD_API_TOKEN" in os.environ else \
        data['jumpcloud_api']['credentials']['token']
        self.jumpcloud_org_id = os.getenv("JUMPCLOUD_ORG_ID") if "JUMPCLOUD_ORG_ID" in os.environ else \
        data['jumpcloud_api']['credentials'].get('org_id', None)
        self.headers = {
            "accept": "application/json",
            "x-api-key": self.jumpcloud_token,
            "content-type": "application/json"
        }
        # Include 'x-org-id' header if 'org_id' is provided
        if self.jumpcloud_org_id:
            self.headers['x-org-id'] = self.jumpcloud_org_id

        # Get time_interval and ensure it's a valid integer
        self.jumpcloud_time_interval = data['jumpcloud_api']['settings'].get('time_interval')
        if not self.jumpcloud_time_interval:
            self.jumpcloud_time_interval = 5  # Default to 5 minutes
        else:
            try:
                self.jumpcloud_time_interval = int(self.jumpcloud_time_interval)
            except ValueError:
                logger.error("Invalid time_interval value in configuration. It must be an integer.")
                return False

        self.logzio_shipper = LogzioShipper(self.logzio_url, self.logzio_token)
        return True

    def write_last_time_to_file(self, last_time_event: str) -> None:
        with open(self.last_start_dates_file, 'w') as f:
            f.write(last_time_event)

    class logzio_error(Exception):
        pass

    def send_events_to_logzio(self, events) -> None:
        """
        Sends a list of events to Logz.io.

        :param events: The list of events to send to Logz.io.
        """
        try:
            if len(events) != 0:
                logger.info("Events number: {}".format(len(events)))
                for event in events:
                    event["@timestamp"] = event["timestamp"]
                    if "changes" in event:
                        event["changes"] = self.changesValueToJSON(event["changes"])
                        event_str = json.dumps(event)
                    else:
                        event_str = json.dumps(event)
                    self.logzio_shipper.add_log_to_send(event_str)

                self.logzio_shipper.send_to_logzio()
                self.last_time_event = events[-1]['timestamp']
            else:
                logger.info("No events")
        except requests.HTTPError as e:
            status_code = e.response.status_code

            if status_code == 400:
                raise self.logzio_error("The logs are badly formatted. response: {}".format(e))

            if status_code == 401:
                raise self.logzio_error("The token is missing or not valid. Make sure you’re using the right account token.")

            raise self.logzio_error("Something went wrong. response: {}".format(e))
        except Exception as e:
            raise self.logzio_error("Failed to send data to Logz.io... {}".format(e))

    class jumpcloud_api_error(Exception):
        pass

    def request_events_jumpcloud(self):
        body = {
            "service": ["all"],
            "start_time": self.last_time_event,
        }
        logger.info("Requesting events from JumpCloud")
        try:
            response = requests.request("POST", self.jumpcloud_url, json=body, headers=self.headers)
            response.raise_for_status()
            return json.loads(response.content.decode('utf-8'))

        except requests.exceptions.HTTPError as errh:
            logger.error(f"HTTP Error occurred: {errh}")
            logger.error(f"Response status code: {response.status_code}")
            logger.error(f"Response content: {response.content}")
            if response.status_code == 401:
                raise self.jumpcloud_api_error("HTTP Error: 401 Unauthorized (Invalid API Key)")
            elif response.status_code == 402:
                raise self.jumpcloud_api_error("HTTP Error: 402 Directory Insights is not enabled for your organization")
            elif response.status_code == 400:
                raise self.jumpcloud_api_error("HTTP Error: 400 Invalid/unknown query JSON body")
            elif response.status_code == 403:
                raise self.jumpcloud_api_error(
                    "HTTP Error: 403 Forbidden. Access is denied. Possible causes include insufficient permissions, invalid credentials, or a missing 'x-org-id' header for organization access."
                )
            else:
                raise self.jumpcloud_api_error(f"HTTP Error: {errh}")
        except requests.exceptions.ConnectionError as errc:
            raise self.jumpcloud_api_error(f"Error Connecting: {errc}")
        except requests.exceptions.Timeout as errt:
            raise self.jumpcloud_api_error(f"Timeout Error: {errt}")
        except requests.exceptions.RequestException as err:
            raise self.jumpcloud_api_error(f"Something went wrong: {err}")
        except Exception as e:
            raise self.jumpcloud_api_error(f"Something went wrong: {e}")

    def run(self):
        signal.signal(signal.SIGINT, self.handle_sigint)
        if not self.read_config():
            return
        while True:
            try:
                events = self.request_events_jumpcloud()
                self.send_events_to_logzio(events)
            except self.jumpcloud_api_error as e:
                logger.error(e)
            except self.logzio_error as e:
                logger.error(e)
            logger.debug("Going to sleep for {}m".format(self.jumpcloud_time_interval))
            time.sleep(self.jumpcloud_time_interval * 60)

