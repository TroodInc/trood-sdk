import json

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
