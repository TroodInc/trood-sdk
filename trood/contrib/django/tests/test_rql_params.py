import django
import pytest
from django.conf import settings
from django.db.models import Q, Model, CharField


class MockSettings:
    REST_FRAMEWORK = {}
    DEBUG = True
    INSTALLED_APPS = ['trood.contrib.django.tests']
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
    EMAIL_BACKEND = []
    ALLOWED_HOSTS = []
    USE_I18N = []
    SERVICE_DOMAIN = "TEST"
    LANGUAGE_CODE = []
    DEFAULT_INDEX_TABLESPACE = []
    CACHES = []
    MIGRATION_MODULES = []

if not settings.configured:
    settings.configure(default_settings=MockSettings)

from trood.contrib.django.filters import TroodRQLFilterBackend
from django.http import HttpRequest
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from django.test import TestCase
import pytest
from rest_framework.test import APIRequestFactory
from rest_framework import generics, renderers, serializers, status
from django.db import models


django.setup()
factory = APIRequestFactory()


class BasicModel(Model):
    text = models.CharField(
        max_length=100,
    )

    class Meta:
        app_label = 'trood.contrib.django.tests'


class BasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicModel
        fields = '__all__'


class RootView(generics.ListCreateAPIView):
    queryset = BasicModel.objects.all()
    serializer_class = BasicSerializer


class TestFilterBackendAppliedToViews(TestCase):
    def setUp(self):
        """
        Create 3 BasicModel instances to filter on.
        """
        items = ['foo', 'bar', 'baz']
        for item in items:
            BasicModel(text=item).save()
        self.objects = BasicModel.objects
        self.data = [
            {'id': obj.id, 'text': obj.text}
            for obj in self.objects.all()
        ]

    def test_filter_backend(self):
        """
        GET requests to ListCreateAPIView should return filtered list.
        """
        root_view = RootView.as_view(filter_backends=(TroodRQLFilterBackend,))
        request = factory.get('/')
        response = root_view(request).render()
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data == [{'id': 1, 'text': 'foo'}]
