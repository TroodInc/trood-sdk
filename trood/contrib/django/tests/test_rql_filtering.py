from unittest import mock

import django
from django.conf import settings
from django.db.models import Q, Model, CharField, QuerySet
from rest_framework.test import APIRequestFactory

from trood.contrib.django.pagination import TroodRQLPagination
from trood.contrib.django.tests.settings import MockSettings

request_factory = APIRequestFactory()

if not settings.configured:
    settings.configure(default_settings=MockSettings)
from trood.contrib.django.filters import TroodRQLFilterBackend
django.setup()


class MockModel(Model):
    name = CharField()
    status = CharField()
    color = CharField()


def test_sort_parameter():
    rql = 'sort(-name,+id, test)'
    ordering = TroodRQLFilterBackend.get_ordering(rql)

    assert ordering == ['-name', 'id', 'test']


def test_like_filter():
    rql = 'like(name,"*23 test*")'
    filters = TroodRQLFilterBackend.parse_rql(rql)

    assert filters == [['like', 'name', '*23 test*']]

    queries = TroodRQLFilterBackend.make_query(filters)

    assert queries == [Q(('name__like', '*23 test*'))]

    assert str(MockModel.objects.filter(*queries).only('id', 'name').query) == 'SELECT "tests_mockmodel"."id", "tests_mockmodel"."name" FROM "tests_mockmodel" WHERE "tests_mockmodel"."name" LIKE %23 test% ESCAPE \'\\\''


def test_boolean_args():
    expected_true = [['exact', 'field', True]]

    assert TroodRQLFilterBackend.parse_rql('eq(field,True())') == expected_true
    assert TroodRQLFilterBackend.parse_rql('eq(field,true())') == expected_true
    assert TroodRQLFilterBackend.parse_rql('eq(field,True)') == expected_true
    assert TroodRQLFilterBackend.parse_rql('eq(field,true)') == expected_true

    expected_false = [['exact', 'field', False]]

    assert TroodRQLFilterBackend.parse_rql('eq(field,False())') == expected_false
    assert TroodRQLFilterBackend.parse_rql('eq(field,false())') == expected_false
    assert TroodRQLFilterBackend.parse_rql('eq(field,False)') == expected_false
    assert TroodRQLFilterBackend.parse_rql('eq(field,false)') == expected_false


def test_date_args():
    rql = "and(ge(created,2020-04-27T00:00:00.0+03:00),le(created,2020-05-03T23:59:59.9+03:00))"
    filters = TroodRQLFilterBackend.parse_rql(rql)

    assert filters == [['AND', ['gte', 'created', '2020-04-27T00:00:00.0+03:00'], ['lte', 'created', '2020-05-03T23:59:59.9+03:00']]]


def test_default_grouping():
    rql = "eq(deleted,0),ge(created,2020-04-27T00:00:00.0+03:00),le(created,2020-05-03T23:59:59.9+03:00),sort(+id),limit(0,10)"

    filters = TroodRQLFilterBackend.parse_rql(rql)
    assert filters == [['AND', ['exact', 'deleted', '0'], ['gte', 'created', '2020-04-27T00:00:00.0+03:00'], ['lte', 'created', '2020-05-03T23:59:59.9+03:00']]]


def test_mixed_grouping():
    rql = 'eq(deleted,0),or(eq(color,"red"),eq(status,2)),sort(+id),limit(0,10)'

    filters = TroodRQLFilterBackend.parse_rql(rql)
    assert filters == [['AND', ['exact', 'deleted', '0'], ['OR', ['exact', 'color', 'red'], ['exact', 'status', '2']]]]


@mock.patch.object(QuerySet, "count")
def test_rql_in_multiple_params(mocked_count):
    request = request_factory.get('/?rql=eq(status,1)&rql=in(color,(red,blue))&rql=limit(0,5)&rql=sort(id)')

    qs = TroodRQLFilterBackend().filter_queryset(request, MockModel.objects.all(), None)
    mocked_count.return_value = 10

    qs = TroodRQLPagination().paginate_queryset(qs, request, None)

    assert str(qs.query) == 'SELECT "tests_mockmodel"."id", "tests_mockmodel"."name", "tests_mockmodel"."status", "tests_mockmodel"."color" FROM "tests_mockmodel" WHERE ("tests_mockmodel"."status" = 1 AND "tests_mockmodel"."color" IN (red, blue)) ORDER BY "tests_mockmodel"."id" ASC LIMIT 5'