import django
from django.conf import settings
from django.db.models import Model, IntegerField
from django.http import HttpRequest
from rest_framework.response import Response

from trood.contrib.django.auth.engine import TroodABACEngine
from trood.contrib.django.tests.settings import MockSettings


if not settings.configured:
    settings.configure(default_settings=MockSettings)
django.setup()

from rest_framework.views import APIView
from rest_framework.test import APIRequestFactory
from trood.contrib.django.auth.permissions import TroodABACPermission

request_factory = APIRequestFactory()


class MockModelOnlyID(Model):
    pass


class MyView(APIView):
    permission_classes = (TroodABACPermission, )

    def get(self, request):
        return Response({"id": 1}, 200)


def test_wildcard_rules():
    denied_view = MyView()
    denied_view.basename = 'DeniedView'
    denied_view.action = 'get'

    allowed_view = MyView()
    allowed_view.basename = 'AllowedView'
    allowed_view.action = 'get'

    request = HttpRequest()
    request.method = 'get'
    request.user = None

    setattr(request, 'abac', TroodABACEngine({
        "TEST": {
            "DeniedView": {"*": [{"result": "deny", "rule": {}, "mask": []}]},
            "AllowedView": {"*": [{"result": "allow", "rule": {}, "mask": []}]},
        }
    }))
    request.data = None

    response = denied_view.dispatch(request)
    assert response.status_code == 403

    response = allowed_view.dispatch(request)
    assert response.status_code == 200


def test_wildcard_sbj_id_rule_filter():
    view = MyView()
    view.basename = 'TestView'
    view.action = 'list'

    request = HttpRequest()
    request.method = 'get'
    request.user = {"id": 1}

    setattr(request, 'abac', TroodABACEngine({"TEST": {
        "_default_resolution": "deny",
        "TestView":
            {"*": [{
                "result": "allow",
                "rule": {"obj.id": "sbj.id"}
            }]}}}))
    request.data = None
    request.abac.check_permited(request, view)
    query = MockModelOnlyID.objects.filter(*request.abac.filters).query
    assert str(query) == 'SELECT "tests_mockmodelonlyid"."id" FROM "tests_mockmodelonlyid" WHERE "tests_mockmodelonlyid"."id" = 1'