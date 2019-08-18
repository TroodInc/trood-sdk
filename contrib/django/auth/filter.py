from rest_framework import filters


class TroodABACFilterBackend(filters.BaseFilterBackend):

    def filter_queryset(self, request, queryset, view):
        return request.abac.filter_data(queryset)
