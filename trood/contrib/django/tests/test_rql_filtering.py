from django.conf import settings
from django.db.models import Q


class MockSettings:
    REST_FRAMEWORK = {}
    DEBUG = True

settings.configure(default_settings=MockSettings)
from trood.contrib.django.filters import TroodRQLFilterBackend


def test_sort_parameter():
    rql = 'sort(-name,+id)'
    ordering = TroodRQLFilterBackend.get_ordering(rql)

    assert ordering == ['-name', 'id']


def test_like_filter():
    rql = 'like(name,"test")'
    filters = TroodRQLFilterBackend.parse_rql(rql)

    assert filters == [['contains', 'name', 'test']]

    queries = TroodRQLFilterBackend.make_query(filters)

    assert queries == [Q(('name__contains', 'test'))]


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
