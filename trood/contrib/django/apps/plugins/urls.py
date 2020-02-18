from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from trood.contrib.django.apps.plugins import views

router = DefaultRouter()

router.register(r'plugins', views.TroodPluginsViewSet)

urlpatterns = [
    url(r'^api/v1.0/', include((router.urls, 'trood_plugins'), namespace='plugins-api')),
]
