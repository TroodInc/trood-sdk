from rest_framework import serializers

from trood.contrib.django.apps.plugins.models import TroodPluginModel


class TroodPluginSerizalizer(serializers.ModelSerializer):
    class Meta:
        model = TroodPluginModel
        fields = '__all__'
