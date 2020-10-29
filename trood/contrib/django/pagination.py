import re

from rest_framework.response import Response
from rest_framework.pagination import BasePagination
from rest_framework.settings import api_settings
from django.conf import settings


class TroodRQLPagination(BasePagination):
    default_limit = api_settings.PAGE_SIZE

    query_param = getattr(settings, 'RQL_FILTER_QUERY_PARAM', 'rql')

    def get_paginated_response(self, data):
        return Response({'data': data, 'total_count': self.count})

    def paginate_queryset(self, queryset, request, view=None):
        self.count = self.get_count(queryset)
        offset, limit = self.get_limit_offset(request)

        if limit is None:
            return None

        if self.count == 0 or offset > self.count:
            return []
        return queryset[offset:offset + limit]

    def get_count(self, queryset):
        """
        Determine an object count, supporting either querysets or regular lists.
        """
        try:
            return queryset.count()
        except (AttributeError, TypeError):
            return len(queryset)

    def get_limit_offset(self, request):
        if self.query_param in request.GET:
            limit_parsed = re.search(
                'limit\((?P<offset>\d+),\s*(?P<limit>\d+)\)', ','.join(
                    request.GET.getlist(self.query_param, [])
                )
            )

            if limit_parsed:
                groups = limit_parsed.groups()

                if len(groups) == 2:
                    return int(groups[0]), int(groups[1])

        return 0, self.default_limit
