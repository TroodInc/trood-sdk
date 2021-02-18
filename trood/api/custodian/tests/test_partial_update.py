from hamcrest import *
import pytest

from trood.api.custodian.client import Client
from trood.api.custodian.records.model import Record
from hamcrest import assert_that, equal_to, contains_string, instance_of


@pytest.mark.integration
def test_client_updates_record_with_partial_data(client: Client):
    record = Record(obj='person', age=20, name='Ivan', is_active=True, street="Street")
    record = client.records.create(record)
    assert_that(record, instance_of(Record))

    # perform partial update
    record = client.records.partial_update('person', record.get_pk(), {'name': 'Petr'})
    assert_that(record.name, equal_to('Petr'))

    # check that new data got stored in Custodian
    record = client.records.get('person', record.get_pk())
    assert_that(record.name, equal_to('Petr'))
