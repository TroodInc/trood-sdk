import glob
import json
import importlib

from django.conf import settings
from django.apps import AppConfig


class TroodPluginsConfig(AppConfig):
    name = 'trood.contrib.django.apps.plugins'
    verbose_name = "Trood Plugins"

    @classmethod
    def ready(cls):
        try:
            from trood.contrib.django.apps.plugins.models import TroodPluginModel
            from trood.contrib.django.apps.plugins.core import TroodBasePlugin

            plugins = [
                module[:-3].replace("/", ".") for module in glob.glob(
                    '{}/*.py'.format(settings.TROOD_PLUGINS_PATH)
                )
            ]

            for plugin in plugins:
                importlib.import_module(plugin)

            for plugin in TroodBasePlugin.__subclasses__():
                obj, created = TroodPluginModel.objects.get_or_create(
                    pk=plugin.id, name=plugin.name, version=plugin.version
                )

                plugin_config = json.dumps(plugin.default_config)
                if created:
                    obj.config = plugin_config
                    obj.save()
                elif obj.config != plugin_config:
                    obj.config = plugin_config
                    obj.save()

                plugin.register()
        except Exception as e:
            print("Can't load plugins, exception: {}".format(e))

