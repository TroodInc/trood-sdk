import json
from django.apps import apps
from trood.contrib.django.apps.plugins.apps import TroodPluginsConfig

from trood.contrib.django.apps.plugins.models import TroodPluginModel


class TroodBasePlugin:
    id = None
    default_config = {}

    @classmethod
    def get_config(cls, key=None):
        config = cls.default_config
        try:
            plugin_config = TroodPluginModel.objects.get(pk=cls.id)
            config = json.loads(plugin_config.config)
        except Exception:
            pass

        if key:
            return config.get(key, None)
        else:
            return config

    @classmethod
    def register(cls):
        raise NotImplementedError()

    @classmethod
    def expose_command(cls, name, handler):
        if cls.id not in apps.app_configs[TroodPluginsConfig.name].plugin_commands:
            apps.app_configs[TroodPluginsConfig.name].plugin_commands[cls.id] = {}

        apps.app_configs[TroodPluginsConfig.name].plugin_commands[cls.id][name] = handler
