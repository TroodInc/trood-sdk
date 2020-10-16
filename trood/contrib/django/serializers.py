from rest_framework import serializers


class TroodDynamicSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(TroodDynamicSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request', None)
        if self.fields and request:
            exclude = request.GET.get('exclude', None)
            only = request.GET.get('only', None)
            if exclude:
                for a in exclude.split(','):
                    self.fields.pop(a)
            elif only:
                only = only.split(',')
                keys = list(self.fields.keys())
                for a in keys:
                    if a not in only:
                        self.fields.pop(a)
