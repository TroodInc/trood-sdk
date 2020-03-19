from django.conf.urls import include, url
from rest_framework.routers import DefaultRouter

from trood.contrib.django.apps.fixtures import views

router = DefaultRouter()

router.register(r'fixtures', views.TroodFixturesViewSet)

urlpatterns = [
    url(r'^api/v1.0/', include((router.urls, 'trood_fixtures'), namespace='fixtures-api')),
]
