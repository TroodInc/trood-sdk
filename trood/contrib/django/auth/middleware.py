import json

import requests
from django.conf import settings

from trood.core.utils import get_service_token

from trood.contrib.django.auth.engine import TroodABACEngine


class TroodABACMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rules = {}
        if settings.TROOD_ABAC['RULES_SOURCE'] == 'FILE':
            with open(settings.TROOD_ABAC['RULES_PATH']) as fp:
                rules = json.load(fp)
        elif settings.TROOD_ABAC['RULES_SOURCE'] == 'URL':
            response = requests.get(
                settings.TROOD_ABAC['RULES_PATH'],
                params={"domain": settings.SERVICE_DOMAIN},
                headers={"Authorization": get_service_token()},
            )
            response.raise_for_status()

            rules = response.json().get('data')

        engine = TroodABACEngine(rules)
        setattr(request, "abac", engine)

        response = self.get_response(request)

        return response
