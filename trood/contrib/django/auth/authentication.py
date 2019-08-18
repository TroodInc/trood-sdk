import requests
import os
from requests import HTTPError
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import exceptions

from core.utils import get_service_token


class TroodUser(object):
    def __init__(self, object):
        for k, v in object.items():
            self.__setattr__(k, v)

    @property
    def is_authenticated(self):
        return True


class TroodTokenAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth = get_authorization_header(request)

        parts = auth.decode('utf-8').split()

        if not parts or len(parts) != 2:
            return None

        try:

            # @todo: extract, load url from settings
            token_type = "service" if parts[0] == "Service" else "user"

            response = requests.post(
                "{}api/v1.0/verify-token/".format(os.environ.get('TROOD_AUTH_SERVICE_URL')),
                data={
                    "type": token_type,
                    "token": parts[1]
                },
                headers={"Authorization": get_service_token()},
            )

            response.raise_for_status()
            response_decoded = response.json()
            user = TroodUser(response_decoded['data'])

            return user, parts[1]

        except HTTPError:
            raise exceptions.AuthenticationFailed()
