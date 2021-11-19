import re
from django.core.exceptions import FieldDoesNotExist
from django.http import HttpRequest
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.urls import get_resolver, URLPattern, URLResolver
from trood.contrib.django.auth.engine import TroodABACEngine


class TroodMetaView(APIView):
    permission_classes = (AllowAny,)

    basename = "meta"

    models_map = {}

    def get(self, request):
        data = {
            "endpoints": {},
            "arrayDataAddress": "data",
            "arrayCountAddress": "total_count",
        }

        self.get_models_map(get_resolver().url_patterns)
        for url in get_resolver().url_patterns:
            if type(url) == URLPattern and url.name:
                endpoint = self.get_endpoint_meta(url)
                data["endpoints"][url.name] = endpoint

            if type(url) == URLResolver:
                for sub in url.url_patterns:
                    endpoint = self.get_endpoint_meta(sub, prefix=str(url.pattern))
                    data["endpoints"][sub.name] = endpoint

        return Response(data)

    def get_models_map(self, urls):
        """
        Getting model-name -> url-name pairs from views with ModelSerializers
        for future fk() field matching
        """
        for url in urls:
            if type(url) == URLResolver:
                for sub in url.url_patterns:
                    if hasattr(sub.callback, 'cls'):
                        view_cls = getattr(sub.callback, 'cls')
                        view = view_cls()
                        if hasattr(view, 'serializer_class'):
                            self.models_map[view.serializer_class.Meta.model.__name__] = sub.name

    def get_endpoint_meta(self, url, prefix=""):
        if url.name == 'api-root':
            return None

        # Cleaning Django url format from regex
        pattern = str(url.pattern)
        pattern = pattern.replace('\\.(?P<format>[a-z0-9]+)/?', '/').replace('$', '')

        # But preserve arguments for future use
        matcher = re.compile(r'\(\?P<([a-z]+)>[^)]+\)')
        args = matcher.findall(pattern)
        pattern = prefix + matcher.sub('{{\\1}}', pattern)

        endpoint = {
            "endpoint":  pattern.replace('^', ''),
            "args": args,
            "methods": {}
        }

        r = HttpRequest()
        r.method = 'OPTIONS'
        r.abac = TroodABACEngine()
        view = None

        # There two types of urls:
        if hasattr(url.callback, 'cls'):
            # With class based view
            view_cls = getattr(url.callback, 'cls')
            view = view_cls()
        else:
            # Or with method based view
            response = url.callback(r)
            if hasattr(response, 'renderer_context'):
                view = response.renderer_context['view']

        # Two types of actions
        if hasattr(url.callback, 'actions'):
            # Altered from ViewSet
            methods = getattr(url.callback, 'actions')
            for k, v in methods.items():
                endpoint['methods'][k.upper()] = v
        elif view is not None:
            # Set by decorator or extended from ApiView
            for method in view.allowed_methods:
                endpoint['methods'][method] = ''

        if view is not None and hasattr(view, 'serializer_class'):
            endpoint['fields'] = {}
            model = view.serializer_class.Meta.model()
            endpoint['pk'] = model._meta.pk.name
            for field_name in view.serializer_class.Meta.fields:
                if hasattr(view.serializer_class, field_name):
                    field = getattr(view.serializer_class, field_name)
                    endpoint['fields'][field_name] = field.type
                    print(getattr(view.serializer_class, field_name))
                else:
                    try:
                        field = model._meta.get_field(field_name)
                        endpoint['fields'][field_name] = self.get_field_type(field)
                    except FieldDoesNotExist:
                        print(f"Cant determine {field_name} field")

        return endpoint

    def get_field_type(self, field):
        internal_type = field.get_internal_type()

        if internal_type in ("CharField", "TextField"):
            return 'string'
        if internal_type == 'BooleanField':
            return 'boolean'
        if internal_type == 'ForeignKey':
            rel_name = field.related_model.__name__
            return f'fk({self.models_map.get(rel_name, rel_name)})'
        if internal_type in ('AutoField', 'IntegerField', 'DecimalField'):
            return 'number'
        if internal_type == 'DateTimeField':
            return 'datetime'

        return internal_type


