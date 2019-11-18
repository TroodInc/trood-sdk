import requests
from django.conf import settings

from django.core.mail.message import EmailMessage
from django.core.mail.backends.smtp import EmailBackend
from trood.core.utils import get_service_token


class TroodEmailMessageTemplate(EmailMessage):
    def __init__(self, data=None, template=None, **kwargs):
        super().__init__(**kwargs)

        self.template = template
        self.data = data


class TroodEmailBackend(EmailBackend):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.mail_service_url = settings.MAIL_SERVICE_URL
        self.headers = {
            "Content-Type": "application/json", "Authorization": get_service_token()
        }

    def send_messages(self, email_messages):
        for message in email_messages:
            if isinstance(message, TroodEmailMessageTemplate):
                self._send_from_template(message)
            else:
                self._send_simple_mail(message)

    def _send_from_template(self, email_message: TroodEmailMessageTemplate):
        requests.post(
            f"{self.mail_service_url}/api/v1.0/mails/from_template/",
            headers=self.headers,
            json={
                # @todo: Remove hardcoded "mailbox" after implementing DEFAULT attribute for mailbox in TroodMail
                "mailbox": 1,
                "to": email_message.to,
                "bcc": email_message.bcc,
                "data": email_message.data,
                "template": email_message.template,
                "from_address": email_message.from_email
            }
        )

    def _send_simple_mail(self, email_message: EmailMessage):
        requests.post(
            f"{self.mail_service_url}/api/v1.0/mails/",
            headers=self.headers,
            json={
                # @todo: Remove hardcoded "mailbox" after implementing DEFAULT attribute for mailbox in TroodMail
                "mailbox": 1,
                "to": email_message.to,
                "bcc": email_message.bcc,
                "subject": email_message.subject,
                "body": email_message.body,
                "from_address": email_message.from_email
            }
        )
