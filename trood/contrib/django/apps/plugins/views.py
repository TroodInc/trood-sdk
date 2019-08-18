from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from trood.contrib.django.apps.plugins.models import TroodPluginModel
from trood.contrib.django.apps.plugins.serialiers import TroodPluginSerizalizer


class TroodPluginsViewSet(viewsets.ModelViewSet):
    queryset = TroodPluginModel.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = TroodPluginSerizalizer
