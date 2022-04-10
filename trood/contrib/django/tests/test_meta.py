from django.conf.urls import url
from django.db import models
from django.urls import include
from rest_framework import viewsets, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.views import APIView

from trood.contrib.django.apps.meta.views import TroodMetaView


class TestModel(models.Model):
    name = models.CharField(max_length=32)


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestModel
        fields = ('id', 'name')


class TestViewSet(viewsets.ModelViewSet):
    serializer_class = TestSerializer


class TestAPIView(APIView):
    def delete(self, request):
        return Response(status=204)


def view_test(request):
    return Response(status=200)


@api_view(['GET', 'POST'])
def view_test_partial(request):
    return Response(status=201)


def test_can_resolve_url_name_to_model_name():
    router = DefaultRouter()
    router.register(r'test-view', TestViewSet, basename='test')

    urlpatterns = [
        url(r'^api/v1.0/', include((router.urls, 'test_meta'), namespace='test-api')),
    ]

    resolver = TroodMetaView()
    resolver.get_models_map(urlpatterns)

    assert resolver.models_map['TestModel'] == 'test-detail'


def test_can_resolve_type_char_field():
    resolver = TroodMetaView()

    test_field = models.CharField(max_length=32)
    assert resolver.get_field_type(test_field) == 'string'


def test_can_resolve_type_text_field():
    resolver = TroodMetaView()

    test_field = models.TextField()
    assert resolver.get_field_type(test_field) == 'string'


def test_can_resolve_type_auto_field():
    resolver = TroodMetaView()

    test_field = models.AutoField()
    assert resolver.get_field_type(test_field) == 'number'


def test_can_resolve_type_integer_field():
    resolver = TroodMetaView()

    test_field = models.IntegerField()
    assert resolver.get_field_type(test_field) == 'number'


def test_can_resolve_type_decimal_field():
    resolver = TroodMetaView()

    test_field = models.DecimalField()
    assert resolver.get_field_type(test_field) == 'number'


def test_can_resolve_type_foreign_key_field():
    router = DefaultRouter()
    router.register(r'test-view', TestViewSet, basename='test')

    urlpatterns = [
        url(r'^api/v1.0/', include((router.urls, 'test_meta'), namespace='test-api')),
    ]

    resolver = TroodMetaView()
    resolver.get_models_map(urlpatterns)

    test_field = models.ForeignKey(TestModel, on_delete=models.SET_NULL)
    assert resolver.get_field_type(test_field) == 'fk(test-detail)'


def test_can_resolve_type_many_to_many_field():
    router = DefaultRouter()
    router.register(r'test-view', TestViewSet, basename='test')

    urlpatterns = [
        url(r'^api/v1.0/', include((router.urls, 'test_meta'), namespace='test-api')),
    ]

    resolver = TroodMetaView()
    resolver.get_models_map(urlpatterns)

    test_field = models.ManyToManyField(TestModel)
    assert resolver.get_field_type(test_field) == 'fk_array(test-detail)'


def test_can_resolve_viewset():
    router = DefaultRouter()
    router.register(r'test-view', TestViewSet, basename='test')

    urlpatterns = [
        url(r'^api/v1.0/', include((router.urls, 'test_meta'), namespace='test-api')),
    ]

    resolver = TroodMetaView()
    resolver.get_models_map(urlpatterns)

    urls = router.get_urls()

    endpoint = resolver.get_endpoint_meta(urls[0])

    assert endpoint['fields'] == {"id": "number", "name": "string"}
    assert endpoint['methods'] == {'GET': 'list', 'POST': 'create'}

    # DRF adds additional urls for type fetching so the next is 2nd index
    endpoint = resolver.get_endpoint_meta(urls[2])

    assert endpoint['methods'] == {'DELETE': 'destroy', 'GET': 'retrieve', 'PATCH': 'partial_update', 'PUT': 'update'}


def test_can_resolve_apiview():
    test_url = url(r'test-view', TestAPIView.as_view(), name='test')

    resolver = TroodMetaView()
    endpoint = resolver.get_endpoint_meta(test_url)

    assert endpoint['methods'] == {'DELETE': '', 'OPTIONS': ''}


def test_can_resolve_functionview():
    test_url = url(r'test-view', view_test, name='test')

    resolver = TroodMetaView()
    endpoint = resolver.get_endpoint_meta(test_url)

    assert endpoint['methods'] == {}

    test_partial_url = url(r'test-view', view_test_partial, name='test')

    endpoint = resolver.get_endpoint_meta(test_partial_url)

    assert endpoint['methods'] == {'GET': '', 'OPTIONS': '', 'POST': ''}
