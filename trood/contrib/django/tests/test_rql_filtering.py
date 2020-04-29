import django
from django.conf import settings
from django.db.models import Q, Model, CharField

class MockSettings:
    REST_FRAMEWORK = {}
    DEBUG = True
    INSTALLED_APPS = ['trood.contrib.django.tests']
    LOGGING_CONFIG = {}
    LOGGING = {}
    SECRET_KEY = ''
    FORCE_SCRIPT_NAME = ''
    DEFAULT_TABLESPACE = ''
    DATABASE_ROUTERS = []
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydatabase',
    }}
    ABSOLUTE_URL_OVERRIDES = {}

settings.configure(default_settings=MockSettings)
from trood.contrib.django.filters import TroodRQLFilterBackend
django.setup()


class MockModel(Model):
    name = CharField()


def test_sort_parameter():
    rql = 'sort(-name,+id, test)'
    ordering = TroodRQLFilterBackend.get_ordering(rql)

    assert ordering == ['-name', 'id', 'test']


def test_like_filter():
    rql = 'like(name,"*23test*")'
    filters = TroodRQLFilterBackend.parse_rql(rql)

    assert filters == [['like', 'name', '*23test*']]

    queries = TroodRQLFilterBackend.make_query(filters)

    assert queries == [Q(('name__like', '*23test*'))]

    assert str(MockModel.objects.filter(*queries).query) == 'SELECT "tests_mockmodel"."id", "tests_mockmodel"."name" FROM "tests_mockmodel" WHERE "tests_mockmodel"."name" LIKE %23test% ESCAPE \'\\\''


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
