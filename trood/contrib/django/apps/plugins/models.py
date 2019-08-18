from django.db import models


class TroodPluginModel(models.Model):
    id = models.CharField(max_length=128, primary_key=True)
    name = models.CharField(max_length=128)
    version = models.CharField(max_length=32)
    active = models.BooleanField(default=False)
    config = models.TextField()
