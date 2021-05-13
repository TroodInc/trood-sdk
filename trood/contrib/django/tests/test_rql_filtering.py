from unittest import mock
import pytest

import django
from django.conf import settings
from django.db.models import Q, QuerySet
from django.db import connections, models
from django.test import TestCase
from pytest import mark
from rest_framework.test import APIRequestFactory
from rest_framework import exceptions

from trood.contrib.django.pagination import TroodRQLPagination
from trood.contrib.django.tests.settings import MockSettings

request_factory = APIRequestFactory()

if not settings.configured:
    settings.configure(default_settings=MockSettings)
from trood.contrib.django.filters import TroodRQLFilterBackend

django.setup()


class MockRelatedModel(models.Model):
    name = models.CharField(max_length=32)


class MockModel(models.Model):
    objects = None
    owner = models.ForeignKey(MockRelatedModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    status = models.CharField(max_length=32)
    color = models.CharField(max_length=32)
    related = models.ManyToManyField(MockRelatedModel)


class ModelsFilteringTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        with connections['default'].schema_editor() as schema_editor:
            schema_editor.create_model(MockRelatedModel)
            schema_editor.create_model(MockModel)

    @classmethod
    def tearDownClass(cls):
        with connections['default'].schema_editor() as schema_editor:
            schema_editor.delete_model(MockModel)
            schema_editor.delete_model(MockRelatedModel)

    @mark.django_db
    def test_distinct_results(self):
        first = MockRelatedModel.objects.create(id=1, name="First")
        second = MockRelatedModel.objects.create(id=2, name="Second")
        third = MockRelatedModel.objects.create(id=3, name="Third")

        test_model = MockModel.objects.create(owner=first, name='Test', status='ACTIVE', color='RED')
        test_model.related.add(second, third)

        request = request_factory.get('/?rql=or(eq(owner.id,1),eq(related.id,1))')
        rows = TroodRQLFilterBackend().filter_queryset(request, MockModel.objects.all(), None)

        assert len(rows) == 1


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

    assert str(
        MockModel.objects.filter(*queries).only('id', 'name').query
    ) == 'SELECT "tests_mockmodel"."id", "tests_mockmodel"."name" ' \
         'FROM "tests_mockmodel" ' \
         'WHERE "tests_mockmodel"."name" ' \
         'ILIKE %23 test% ESCAPE \'\\\''


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

    assert filters == [
        ['AND', ['gte', 'created', '2020-04-27T00:00:00.0+03:00'], ['lte', 'created', '2020-05-03T23:59:59.9+03:00']]]


def test_default_grouping():
    rql = "eq(deleted,0),ge(created,2020-04-27T00:00:00.0+03:00),le(created,2020-05-03T23:59:59.9+03:00),sort(+id),limit(0,10)"

    filters = TroodRQLFilterBackend.parse_rql(rql)
    assert filters == [['AND', ['exact', 'deleted', '0'], ['gte', 'created', '2020-04-27T00:00:00.0+03:00'],
                        ['lte', 'created', '2020-05-03T23:59:59.9+03:00']]]


def test_mixed_grouping():
    rql = 'eq(deleted,0),or(eq(color,"red"),eq(status,2)),sort(+id),limit(0,10)'

    filters = TroodRQLFilterBackend.parse_rql(rql)
    assert filters == [['AND', ['exact', 'deleted', '0'], ['OR', ['exact', 'color', 'red'], ['exact', 'status', '2']]]]


@mock.patch.object(QuerySet, "count")
def test_rql_in_multiple_params(mocked_count):
    request = request_factory.get('/?rql=eq(status,1)&rql=in(color,(red,blue))&rql=limit(0,5)&rql=sort(id)')

    qs = TroodRQLFilterBackend().filter_queryset(request, MockModel.objects.all(), None)
    mocked_count.return_value = 10

    qs = TroodRQLPagination().paginate_queryset(qs.only('id'), request, None)

    assert str(
        qs.query
    ) == 'SELECT DISTINCT "tests_mockmodel"."id" ' \
         'FROM "tests_mockmodel" ' \
         'WHERE ("tests_mockmodel"."status" = 1 AND "tests_mockmodel"."color" IN (red, blue)) ' \
         'ORDER BY "tests_mockmodel"."id" ASC ' \
         'LIMIT 5'


def test_like_filter_case_insensitive():
    rql = 'like(name,"*23 TEST*")'
    filters = TroodRQLFilterBackend.parse_rql(rql)

    assert filters == [['like', 'name', '*23 TEST*']]

    queries = TroodRQLFilterBackend.make_query(filters)

    assert queries == [Q(('name__like', '*23 TEST*'))]
    assert str(MockModel.objects.filter(*queries).query) == 'SELECT "tests_mockmodel"."id", "tests_mockmodel"."owner_id", "tests_mockmodel"."name", "tests_mockmodel"."status", "tests_mockmodel"."color" FROM "tests_mockmodel" WHERE "tests_mockmodel"."name" ILIKE %23 TEST% ESCAPE \'\\\''


def test_not_eq_filter():
    rql = 'not(eq(name, "test"))'
    filters = TroodRQLFilterBackend.parse_rql(rql)
    queries = TroodRQLFilterBackend.make_query(filters)

    assert str(MockModel.objects.filter(*queries).query) == 'SELECT "tests_mockmodel"."id", "tests_mockmodel"."owner_id", "tests_mockmodel"."name", "tests_mockmodel"."status", "tests_mockmodel"."color" FROM "tests_mockmodel" WHERE NOT ("tests_mockmodel"."name" = test)'


def test_not_in_filter():
    rql = 'not(in(id,(1,2,3)))'
    filters = TroodRQLFilterBackend.parse_rql(rql)
    queries = TroodRQLFilterBackend.make_query(filters)
    assert str(MockModel.objects.filter(*queries).query) == 'SELECT "tests_mockmodel"."id", "tests_mockmodel"."owner_id", "tests_mockmodel"."name", "tests_mockmodel"."status", "tests_mockmodel"."color" FROM "tests_mockmodel" WHERE NOT ("tests_mockmodel"."id" IN (1, 2, 3))'


def test_not_or_filter():
    rql = 'not(or(in(id,(1,2,3)),eq(id, 123)))'
    filters = TroodRQLFilterBackend.parse_rql(rql)
    queries = TroodRQLFilterBackend.make_query(filters)
    assert str(MockModel.objects.filter(*queries).query) == 'SELECT "tests_mockmodel"."id", "tests_mockmodel"."owner_id", "tests_mockmodel"."name", "tests_mockmodel"."status", "tests_mockmodel"."color" FROM "tests_mockmodel" WHERE NOT (("tests_mockmodel"."id" IN (1, 2, 3) OR "tests_mockmodel"."id" = 123))'


def test_rql_invalid_params():
    request = request_factory.get('/?rql=eq(status,')

    with pytest.raises(exceptions.ValidationError):
        TroodRQLFilterBackend().filter_queryset(request, MockModel.objects.all(), None)
