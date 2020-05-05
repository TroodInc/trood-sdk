import json

import django
from django.conf import settings

from trood.contrib.django.auth.engine import TroodABACEngine


class MockSettings:
    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': [],
        'DEFAULT_PERMISSION_CLASSES': [],
        'UNAUTHENTICATED_USER': None,
    }
    INSTALLED_APPS = [
        'trood.contrib.django.tests',
    ]
    DEBUG = True
    LOGGING_CONFIG = {}
    LOGGING = {}
    SECRET_KEY = ''
    FORCE_SCRIPT_NAME = ''
    DEFAULT_TABLESPACE = ''
    DEFAULT_CHARSET = 'utf-8'
    DATABASE_ROUTERS = []
    DATA_UPLOAD_MAX_MEMORY_SIZE = 2621440
    DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydatabase',
    }}
    ABSOLUTE_URL_OVERRIDES = {}
    SERVICE_DOMAIN = "TEST"


settings.configure(default_settings=MockSettings)
django.setup()

from django.http import HttpRequest
from rest_framework.response import Response
from trood.contrib.django.auth.renderers import TroodABACJSONRenderer
from rest_framework.viewsets import ViewSet


class TestView(ViewSet):
    renderer_classes = (TroodABACJSONRenderer, )
    action_map = {'get': 'list', 'post': 'create'}

    def get(self, request):
        return Response([{"field_to_hide": 100, "id": 1}])


def test_can_mask_simple_field():
    view = TestView()
    view.basename = 'TestView'
    view.action = 'list'
    request = HttpRequest()
    request.method = 'get'
    request.user = None

    setattr(request, 'abac', TroodABACEngine({"TEST": {"TestView": {"list": [{
        "result": "allow",
        "rule": {},
        "mask": ["field_to_hide"]
    }]}}}))
    request.data = None
    request.abac.check_permited(request, view)

    response = view.dispatch(request)
    response = view.get_renderers()[0].render(response.data, renderer_context={
        'request': request,
        'response': response,
    })
    assert 'field_to_hide' not in json.loads(response)
