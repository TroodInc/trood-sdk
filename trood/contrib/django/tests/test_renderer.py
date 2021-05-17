import json

import django
from django.conf import settings

from trood.contrib.django.auth.engine import TroodABACEngine
from trood.contrib.django.tests.settings import MockSettings

if not settings.configured:
    settings.configure(default_settings=MockSettings)
django.setup()

from django.http import HttpRequest
from rest_framework.response import Response
from trood.contrib.django.auth.renderers import TroodABACJSONRenderer
from rest_framework.viewsets import ViewSet


class MyView(ViewSet):
    renderer_classes = (TroodABACJSONRenderer, )
    action_map = {'get': 'list', 'post': 'create'}

    def get(self, request):
        return Response([{"field_to_hide": 100, "id": 1}])


def test_can_mask_simple_field():
    view = MyView()
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
    assert 'field_to_hide' not in json.loads(response)[0]
