import datetime
import http.client
import time
import urllib
import os

import pytz
import requests

from dotenv import load_dotenv

load_dotenv()
WEBSITE_URL = os.getenv("WEBSITE_URL")
WEBSITE_NAME = os.getenv("WEBSITE_NAME")
APP_TOKEN = os.getenv("APP_TOKEN")
USER_TOKEN = os.getenv("USER_TOKEN")
INTERVAL = int(os.getenv("INTERVAL"))
TIMEZONE = os.getenv("TIMEZONE")


timezone = pytz.timezone(TIMEZONE)

STATUS_UP, STATUS_DOWN, STATUS_UNKNOWN = range(3)

current_status = STATUS_UNKNOWN
time_of_down: datetime = datetime.datetime(year=1970, month=1, day=1)


def check_website():
    global current_status
    global time_of_down
    try:
        r = requests.get(WEBSITE_URL, allow_redirects=True)
        if r.status_code != 200:  # Site is down
            handle_down_event()
        else:  # Site is up
            handle_up_event()
    except requests.exceptions.RequestException as e:
        handle_down_event(repr(e))


def handle_up_event():
    global current_status
    if current_status == STATUS_DOWN:
        now = datetime.datetime.now(tz=timezone)
        now_ts = int(datetime.datetime.timestamp(now))
        difference = now - time_of_down
        difference_minutes = difference.seconds / 60

        message = WEBSITE_NAME + " is back up after " + str(difference_minutes) + " minutes."
        print(message)
        send_message(content = message, title = WEBSITE_NAME + " is back up", timestamp = now_ts)

    current_status = STATUS_UP


def handle_down_event(exception_message: str = ""):
    global time_of_down
    global current_status

    if current_status != STATUS_DOWN:  # this is the first time we see the website down
        now = datetime.datetime.now(tz=timezone)
        now_ts = int(datetime.datetime.timestamp(now))
        time_of_down = now
        message = WEBSITE_NAME + " is down or cannot be checked at " + str(now) + ". Exception: " + exception_message
        print(message)
        send_message(content = message, title = WEBSITE_NAME + " down", timestamp = now_ts)

    current_status = STATUS_DOWN


def send_message(content: str, title: str = "", timestamp: int = -1):
    raw_params = {
        "token": APP_TOKEN,
        "user": USER_TOKEN,
        "message": content,
        "title": title,
    }
    if timestamp != -1:
        raw_params["timestamp"] = timestamp
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST",
                 "/1/messages.json",
                 urllib.parse.urlencode(raw_params),
                 {"Content-type": "application/x-www-form-urlencoded"})
    conn.getresponse()


if __name__ == '__main__':
    while True:
        check_website()
        time.sleep(INTERVAL)