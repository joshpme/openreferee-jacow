import json
import logging
import threading
from requests.exceptions import HTTPError, ConnectionError, Timeout, RequestException
from .operations import setup_requests_session


class NotifyService:
    def __init__(self, url=None, token=None, logger=None) -> None:
        self.url = url
        self.token = token
        self.logger = logger
        self.session = None

    def log_error(self, *args) -> logging.Logger:
        if self.logger is not None:
            return self.logger.error(*args)

    def send(self, payload):
        try:
            self.session.post(self.url, data=json.dumps({"payload": payload}))
        except HTTPError as e:
            self.log_error("Invalid response from notify: %s", str(e))
        except ConnectionError as e:
            self.log_error("Could not connect to notify server: %s", str(e))
        except Timeout as e:
            self.log_error("Notify server timed out: %s", str(e))
        except RequestException as e:
            self.log_error("Failed to send notify payload %s", str(e))

    def notify(self, payload):
        if self.url is None or self.url == '':
            return

        if self.session is None:
            self.session = setup_requests_session(self.token)

        threading.Thread(target=self.send, args=(payload,)).start()


class NotifyExtension:
    def __init__(self, context=None, notify_url=None, notify_token=None):
        self.url = notify_url
        self.token = notify_token
        self.service = None
        if context is not None:
            self.init_app(context)

    def init_app(self, app):
        app.config.setdefault('NOTIFY_URL', self.url)
        app.config.setdefault('NOTIFY_TOKEN', self.token)

        if app.config['NOTIFY_URL'] not in [None, '']:
            app.logger.info("Enabling notifications to URL %s", app.config['NOTIFY_URL'])
            app.logger.info("Token found: %s", app.config['NOTIFY_TOKEN'] is not None)

            self.service = NotifyService(
                app.config['NOTIFY_URL'],
                app.config['NOTIFY_TOKEN'],
                app.logger,
            )
            app.extensions['notifier'] = self.service
        else:
            app.logger.warn("Skipping notifications, NOTIFY_URL missing in .env")

