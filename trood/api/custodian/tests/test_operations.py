import datetime

import pytest
import requests_mock
from hamcrest import assert_that, has_length, equal_to, not_, contains_string,\
     is_, instance_of, is_not

from trood.api.custodian.client import Client
from trood.api.custodian.exceptions import RecordAlreadyExistsException
from trood.api.custodian.records.model import Record


def test_client_retrieves_existing_record(person_record: Record, client: Client):
    record_data = person_record.data
    record_data['id'] = 99
    with requests_mock.Mocker() as mocker:
        mocker.get(
            '/'.join([client.server_url, 'data/{}/{}'.format(person_record.obj, person_record.get_pk())]),
            json={
                'status': 'OK',
                'data': person_record.data
            }
        )
        record = client.records.get(person_record.obj, person_record.get_pk())
        assert_that(record, is_(instance_of(Record)))


def test_client_returns_none_for_nonexistent_record(person_record: Record, client: Client):
    record_data = person_record.data
    record_data['id'] = 99
    with requests_mock.Mocker() as mocker:
        mocker.get(
            '/'.join([client.server_url, 'data/{}/{}'.format(person_record.obj, person_record.get_pk())]),
            json={
                'status': 'FAIL',
                'data': {}
            }
        )
        record = client.records.get(person_record.obj, person_record.get_pk())
        assert_that(record, is_(None))


def test_client_returns_new_record_on_record_creation(person_record: Record, client: Client):
    person_record.id = None
    assert_that(person_record.exists(), is_not(True))
    record_data = person_record.data
    record_data['id'] = 45
    with requests_mock.Mocker() as mocker:
        mocker.post(
            '/'.join([client.server_url, 'data/{}'.format(person_record.obj)]),
            json={
                'status': 'OK',
                'data': record_data
            }
        )
        record = client.records.create(person_record)
        assert_that(record, is_(instance_of(Record)))
        assert_that(record.exists())
        assert_that(record.id, equal_to(45))


def test_client_deletes(person_record: Record, client: Client):
    record_data = person_record.data
    record_data['id'] = 99
    assert_that(person_record.exists())
    record_data = person_record.data
    with requests_mock.Mocker() as mocker:
        mocker.delete(
            '/'.join([client.server_url, 'data/{}'.format(person_record.obj)]),
            json={
                'status': 'OK',
                'data': record_data
            }
        )
        client.records.delete(person_record)
        assert_that(person_record.exists(), is_not(True))


def test_client_returns_updated_record_on_record_update(person_record: Record, client: Client):
    record_data = person_record.data
    record_data['id'] = 99
    record_data['is_active'] = False
    with requests_mock.Mocker() as mocker:
        mocker.patch(
            '/'.join([client.server_url, 'data/{}'.format(person_record.obj)]),
            json={
                'status': 'OK',
                'data': [record_data]
            }
        )
        record = client.records.update(person_record)
        assert_that(record, is_(instance_of(Record)))
        assert_that(record.exists())
        assert_that(record.is_active, is_(False))


def test_client_returns_iterable_of_records_on_bulk_query(person_record: Record, client: Client):
    query = client.records.query('person').filter(address__city_id__eq=45)
    with requests_mock.Mocker() as mocker:
        mocker.get(
            '/'.join([client.server_url, 'data/person']),
            json={
                'status': 'OK',
                'data': [
                    # nothing terrible in is that records are duplicated
                    person_record.data,
                    person_record.data
                ]
            }
        )
        assert_that(len(query), equal_to(2))
        for record in query:
            assert_that(record, instance_of(Record))


def test_client_returns_list_of_records_on_bulk_create(client: Client):
    records_to_create = [
        Record(
            obj='person',
            name='Ivan Petrov',
            is_active=False,
            street="street",
            age=42
        ),
        Record(
            obj='person',
            name='Nikolay Kozlov',
            is_active=True,
            street="street",
            age=36
        )
    ]

    with requests_mock.Mocker() as mocker:
        mocker.post(
            '/'.join([client.server_url, 'data/person']),
            json={
                'status': 'OK',
                'data': [
                    {**x.data, **{'id': records_to_create.index(x) + 1}} for x in records_to_create
                ]
            }
        )
        created_records = client.records.create(*records_to_create)
        for created_record in created_records:
            assert_that(created_record, instance_of(Record))
            assert_that(created_record.name)


def test_client_returns_list_of_records_on_bulk_update(client: Client):
    records_to_update = [
        Record(
            obj='person',
            name='Ivan Petrov',
            is_active=False,
            age=15,
            id=23,
            street=""
        ),
        Record(
            obj='person',
            name='Nikolay Kozlov',
            is_active=True,
            age=44,
            id=34,
            street=""
        )
    ]

    with requests_mock.Mocker() as mocker:
        mocker.patch(
            '/'.join([client.server_url, 'data/person']),
            json={
                'status': 'OK',
                'data': [x.data for x in records_to_update]
            }
        )
        updated_records = client.records.update(*records_to_update)
        for updated_record in updated_records:
            assert_that(updated_record, instance_of(Record))
            assert_that(updated_record.name)
        assert_that(updated_records, equal_to(records_to_update))


def test_client_returns_list_of_records_without_pk_value_on_bulk_delete(client: Client):
    records_to_delete = [
        Record(
            obj='person',
            name='Ivan Petrov',
            is_active=False,
            id=23
        ),
        Record(
            obj='person',
            name='Nikolay Kozlov',
            is_active=True,
            id=34
        )
    ]

    with requests_mock.Mocker() as mocker:
        mocker.delete(
            '/'.join([client.server_url, 'data/person']),
            json={
                'status': 'OK'
            }
        )
        client.records.delete(*records_to_delete)
        for record in records_to_delete:
            assert_that(not record.exists())


class TestCustodianOperationsIntegrationSeries:
    @pytest.mark.integration
    def test_new_record_is_created(self, person_record: Record, client: Client):
        """
        Create a new record and check it has PK field assigned
        :param person_record:
        :param client:
        """
        person_record = client.records.create(person_record)
        assert_that(person_record.id, instance_of(int))
        assert_that(person_record, instance_of(Record))

    @pytest.mark.integration
    def test_record_cration_with_given_id(self, person_record: Record, client: Client):
        """
        Create a new record with given id
        :param person_record:
        :param client:
        """
        person_record.id = 199
        person_record = client.records.create(person_record)
        assert_that(person_record, instance_of(Record))
        assert_that(person_record.id, equal_to(199))


    @pytest.mark.integration
    def test_new_record_can_be_retrieved_by_pk(self, person_record: Record, client: Client):
        """
        Create a new record and check it has PK field assigned
        :param person_record:
        :param client:
        """
        person_record = client.records.create(person_record)
        assert_that(client.records.get(person_record.obj, person_record.get_pk()), instance_of(Record))

    @pytest.mark.integration
    def test_new_record_is_not_created_if_pk_is_duplicated(self, person_record: Record, client: Client):
        """
        Try to create a new record with duplicated PK. Client should raise exception
        :param person_record:
        :param client:
        """
        # create new record
        person_record = client.records.create(person_record)
        with pytest.raises(RecordAlreadyExistsException):
            client.records.create(person_record)

    @pytest.mark.integration
    def test_record_is_updated(self, person_record: Record, client: Client):
        """
        Change the record`s field value and store this change in the database
        :param person_record:
        :param client:
        """
        person_record = client.records.create(person_record)
        new_name = 'Feodor'
        assert_that(new_name, not_(equal_to(person_record.name)))
        person_record.name = new_name
        person_record = client.records.update(person_record)
        assert_that(person_record, instance_of(Record))
        assert_that(person_record.name, equal_to(new_name))

    @pytest.mark.integration
    def test_record_is_deleted(self, person_record: Record, client: Client):
        """
        Delete the record and verify it does not exist in the database
        :param person_record:
        :param client:
        """
        person_record = client.records.create(person_record)
        pk = person_record.get_pk()
        deleted_record = client.records.delete(person_record)
        assert_that(person_record.get_pk(), is_(None))
        assert_that(client.records.get(person_record.obj, pk), is_(None))
        assert_that(deleted_record, instance_of(Record))

    @pytest.mark.integration
    def test_records_are_created(self, client: Client):
        """
        Create two records and verify pk values are assigned
        :param client:
        """
        first_record = Record(obj='person', **{'name': 'Feodor', 'is_active': True, 'age': 23, "street": "St"})
        second_record = Record(obj='person', **{'name': 'Victor', 'is_active': False, 'age': 22, "street": "St"})
        first_record, second_record = client.records.create(first_record, second_record)
        assert_that(first_record.get_pk(), instance_of(int))
        assert_that(second_record.get_pk(), instance_of(int))
        self._created_records = (first_record, second_record)

    @pytest.mark.integration
    def test_records_are_updated(self, two_records, client: Client):
        """
        Update created records and verify updated values are set
        :param client:
        """
        assert_that(two_records[0].name, not_(equal_to('Petr')))
        assert_that(two_records[1].is_active, is_(False))
        two_records[0].name = 'Petr'
        two_records[1].is_active = True
        client.records.update(*two_records)
        assert_that(two_records[0].name, equal_to('Petr'))
        assert_that(two_records[1].is_active, is_(True))

    @pytest.mark.integration
    def test_records_are_deleted(self, two_records, client: Client):
        """
        Delete created records and verify its pk values are None
        :param client:
        """
        deleted_records = client.records.delete(*two_records)
        assert_that(two_records[0].get_pk(), is_(None))
        assert_that(two_records[1].get_pk(), is_(None))
        assert_that(deleted_records, instance_of(list))

    @pytest.mark.integration
    def test_slice(self, client: Client):
        client.records.delete(*[x for x in client.records.query('person')])
        assert_that(client.records.query('person'), has_length(0))
        client.records.create(
            Record(obj='person', **{'name': 'Feodor', 'is_active': True, 'age': 23, 'street': 'street'}),
            Record(obj='person', **{'name': 'Victor', 'is_active': False, 'age': 22, 'street': 'street'}),
            Record(obj='person', **{'name': 'Artem', 'is_active': True, 'age': 35, 'street': 'street'}),
            Record(obj='person', **{'name': 'Anton', 'is_active': False, 'age': 55, 'street': 'street'})
        )
        assert_that(client.records.query('person'), has_length(4))
        two_first_records = client.records.query('person')[:2]
        assert_that(two_first_records, has_length(2))