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
    ALLOWED_HOSTS = ["*"]
    EMAIL_BACKEND = 'trood.contrib.django.mail.backends.TroodEmailBackend'
    USE_I18N = True
    USE_L10N = True
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydatabase',
    }}
    ABSOLUTE_URL_OVERRIDES = {}


if not settings.configured:
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
    rql = 'like(name,"*23 test*")'
    filters = TroodRQLFilterBackend.parse_rql(rql)

    assert filters == [['like', 'name', '*23 test*']]

    queries = TroodRQLFilterBackend.make_query(filters)

    assert queries == [Q(('name__like', '*23 test*'))]

    assert str(MockModel.objects.filter(*queries).query) == 'SELECT "tests_mockmodel"."id", "tests_mockmodel"."name" FROM "tests_mockmodel" WHERE "tests_mockmodel"."name" ILIKE %23 test% ESCAPE \'\\\''


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


def test_like_filter_case_insensitive():
    rql = 'like(name,"*23 TEST*")'
    filters = TroodRQLFilterBackend.parse_rql(rql)

    assert filters == [['like', 'name', '*23 TEST*']]

    queries = TroodRQLFilterBackend.make_query(filters)

    assert queries == [Q(('name__like', '*23 TEST*'))]

    assert str(MockModel.objects.filter(*queries).query) == 'SELECT "tests_mockmodel"."id", "tests_mockmodel"."name" FROM "tests_mockmodel" WHERE "tests_mockmodel"."name" ILIKE %23 TEST% ESCAPE \'\\\''


def test_not_filter():
    rql = 'not(name, "test")'
    filters = TroodRQLFilterBackend.parse_rql(rql)

    assert filters == [['not', 'name', 'test']]

    queries = TroodRQLFilterBackend.make_query(filters)

    assert queries == [Q(('name__not', 'test'))]
    assert str(MockModel.objects.filter(*queries).query) == 'SELECT "tests_mockmodel"."id", "tests_mockmodel"."name" FROM "tests_mockmodel" WHERE "tests_mockmodel"."name" <> test ESCAPE \'\\\''
