import json

import requests
import os

from django.contrib.auth.models import AnonymousUser
from requests import HTTPError
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework import exceptions
from django_redis import get_redis_connection

from trood.core.utils import get_service_token


class TroodUser(object):
    def __init__(self, object):
        for k, v in object.items():
            self.__setattr__(k, v)

    @property
    def is_authenticated(self):
        return True


class TroodTokenAuthentication(BaseAuthentication):

    def authenticate(self, request):
        auth = get_authorization_header(request).decode('utf-8')
        parts = auth.split()

        if not auth or len(parts) != 2:
            return AnonymousUser(), None

        try:
            user = self.get_user_from_cache(auth)

            if not user:
                user = self.get_user_from_service(auth)

            return user, parts[1]

        except Exception:
            raise exceptions.AuthenticationFailed()

    def get_user_from_cache(self, token):
        cache_type = os.environ.get("CACHE_TYPE", None)

        if cache_type == "REDIS":
            redis = get_redis_connection("default")
            cached_user = redis.get(f"AUTH:{token}")

            if cached_user:
                return TroodUser(json.loads(cached_user))

        return None

    def get_user_from_service(self, token):
        parts = token.split()

        if not parts or len(parts) != 2:
            return None

        try:
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
            return TroodUser(response_decoded['data'])

        except HTTPError:
            raise exceptions.AuthenticationFailed()
