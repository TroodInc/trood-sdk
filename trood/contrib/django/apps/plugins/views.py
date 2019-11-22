from django.apps import apps
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from trood.contrib.django.apps.plugins.models import TroodPluginModel
from trood.contrib.django.apps.plugins.serialiers import TroodPluginSerizalizer


class TroodPluginsViewSet(viewsets.ModelViewSet):
    queryset = TroodPluginModel.objects.all()
    permission_classes = (IsAuthenticated, )
    serializer_class = TroodPluginSerizalizer


def trood_plugin_command(request, plugin_id, command):
    plugins_app = apps.get_app_config('trood.contrib.django.apps.plugins')

    if plugin_id not in plugins_app.commands:
        return Response({"error": f"Plugin {plugin_id} inactive or doesnt exist"}, status=status.HTTP_404_NOT_FOUND)

    if command not in plugins_app.commands[plugin_id]:
        return Response({"error": f"Plugin {plugin_id} has no command [{command}]"}, status=status.HTTP_404_NOT_FOUND)

    return plugins_app.commands[plugin_id](request)
