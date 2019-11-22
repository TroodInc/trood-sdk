from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from trood.contrib.django.apps.plugins import views

router = DefaultRouter()

router.register(r'plugins', views.TroodPluginsViewSet)

urlpatterns = [
    url(r'^/plugins', include(router.urls, namespace='plugins-api')),
    url(r'^/<?>/<?>/', )
]
