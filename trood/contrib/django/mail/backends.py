import requests

from django.core.mail.message import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from trood_auth_client.authentication import get_service_token


class TroodEmailMessage(EmailMessage):
    def __init__(self, subject='', body='', from_email=None, to=None, bcc=None,
                 connection=None, attachments=None, headers=None, cc=None,
                 reply_to=None, data=None, template=None):
        super().__init__(subject, body, from_email, to, bcc, connection,
                         attachments, headers, cc, reply_to)
        if template:
            self.template = template
            self.message_data = data
            self.message_json = self.get_message_json()

    def get_message_json(self):
        message_json = {
            "mailbox": 1,
            "to": self.to,
            "template": self.template
        }
        message_json.update(self.message_data)
        return message_json


class TroodEmailBackend(EmailBackend):
    def __init__(self, host=None, port=None, username=None, password=None,
                 use_tls=None, fail_silently=False, use_ssl=None, timeout=None,
                 ssl_keyfile=None, ssl_certfile=None, custom_mail_service=None):
        super().__init__(host, port, username, password,
                         use_tls, fail_silently, use_ssl, timeout,
                         ssl_keyfile, ssl_certfile)
        self.custom_mail_service = custom_mail_service

        if self.custom_mail_service:
            self.url = f"{self.custom_mail_service}/api/v1.0/mails/from_template/"
            self.headers = {"Content-Type": "application/json",
                            "Authorization": get_service_token()}

    def send_messages(self, email_messages):
        if self.custom_mail_service:
            self._send_custom_messages(email_messages)
        else:
            super().send_messages(email_messages)

    def _send_custom_messages(self, email_messages):
        if not email_messages:
            return 0
        num_sent = 0
        for email_message in email_messages:
            response = requests.post(self.url, json=email_message.message_json,
                                     headers=self.headers)
            response.raise_for_status()
            if response.status_code == 200:
                num_sent += 1
        return num_sent
