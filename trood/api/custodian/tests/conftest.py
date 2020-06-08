import os

import pytest

from trood.api.custodian.client import Client
from trood.api.custodian.records.model import Record


@pytest.fixture
def client():
    return Client(server_url=os.environ.get('SERVER_URL', 'http://localhost:8000/custodian'))


@pytest.fixture
def person_record():
    return Record(obj='person', age=20, name='Ivan', is_active=True, street="Street")



@pytest.fixture
def two_records(client):
    client.records.delete(*[x for x in client.records.query('person')])
    first_record = Record(obj='person',
                          **{'name': 'Feodor', 'is_active': True, 'age': 20, 'street': 'street'})
    second_record = Record(obj='person',
                           **{'name': 'Victor', 'is_active': False, 'age': 40, 'street': 'street'})
    first_record, second_record = client.records.create(first_record, second_record)
    return first_record, second_record

