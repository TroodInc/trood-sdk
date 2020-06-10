Custodian API library
=====================
Description.

Custodian API library allows you to perform basic CRUD operations on custodian records.

Installation.

::

    pip install trood

Setup.

#. Start custodian.
#. Migrate Custodain.


Client
------
Initiate a client.

::

    from trood.api.custodian.client import Client

    AUTH_TOKEN = 'YOUR AUTH TOKEN'
    CUSTODIAN_URL = 'http://localhost:8000/custodian'
    client = Client(server_url=CUSTODIAN_URL, authorization_token=AUTH_TOKEN)
      


.. autoclass:: trood.api.custodian.client.Client
    :show-inheritance:


    .. automethod:: __init__


Record
------
::

    from trood.api.custodian.records.model import Record

    record = Record(obj='person', age=20, name='Ivan', is_active=True, street="Street")

    record.data
    # {'age':20, 'name': 'Ivan', 'is_active': True, 'street': 'Street'}

    record.name
    # 'Ivan'

    record.age
    # 20

    record.id
    # None

    record.exists()
    # if record has id returns True


.. autoclass:: trood.api.custodian.records.model.Record
    :show-inheritance:
    :members:


Record manager
--------------
.. autoclass:: trood.api.custodian.records.manager.RecordsManager
    :show-inheritance:
    

    .. automethod:: get
    .. automethod:: create
    .. automethod:: update
    .. automethod:: delete
    .. automethod:: partial_update


Create Records
--------------
Create single record.
::

    record = Record(obj='person', age=20, name='Ivan', is_active=True, street="Street")
    record = client.records.create(record)

    # after creation record gets id attribute
    record.id
    # 1

    record.exits()
    # True

    type(record)
    # Record


Create several records.
::

    first_record = Record(obj='person', **{'name': 'Feodor', 'is_active': True, 'age': 20, 'street': 'street'})
    second_record = Record(obj='person', **{'name': 'Victor', 'is_active': False, 'age': 40, 'street': 'street'})
    records = client.records.create(first_record, second_record)

    len(records)
    # 2 

    type(records)
    # list



Update Records
--------------
Single record update.
::

    record = Record(obj='person', age=20, name='Ivan', is_active=True, street="Street")
    record = client.records.create(record)

    # set new attribute
    new_name = 'Feodor'
    record.name = new_name

    # update record
    record = client.records.update(record)

    type(record)
    # Record

    
Several records update.
::

    first_record = Record(obj='person', **{'name': 'Feodor', 'is_active': True, 'age': 20, 'street': 'street'})
    second_record = Record(obj='person', **{'name': 'Victor', 'is_active': False, 'age': 40, 'street': 'street'})
    records = client.records.create(first_record, second_record)

    # set new attributes
    first_record_new_name = 'Feodor'
    first_record.name = first_record_new_name
    srcond_record_new_name = 'Feodor'
    second_record.name = first_record_new_name

    # update record
    records = client.records.update(first_record, second_record)

    type(records)
    # list

You can also update records without Record object creation.
::

    # partial update without Record creation.
    record = client.records.partial_update('person', 1, {'name': 'Petr'})


Delete Records
--------------
::

    # id is required
    record.exists()
    # True 

    # delete single record
    client.records.delete(record)

    # delete several records
    client.records.delete(*two_records)


Retrive Record
--------------
You can retrive single record by id.
::

    record = client.records.get('person', 1)


Queries
~~~~~~~
You can also retrive records using Queries.
Custodian API library supports RQL queries. For more inforamtion see: :ref:`rql`.
   
::

    from trood.api.custodian.records.query import Q
    # Known operators 'in', 'like', 'eq', 'ne', 'gt', 'ge', 'lt', 'le'

    records = client.records.query('person').filter(age__gt=18)
    # retrive records with age > 18

    Use to_string method to check rql query
    client.records.query('person').filter(age__gt=18).to_string()
    # gt(age,18)

    records = client.records.query('person').filter(age__gt=18, is_active__eq=False)
    # retrive records with age > 18 and is_active = False


You can also make more complicated queries using Q-expressions.

::

    # nested queries
    records = client.records.query('person').filter(address__city__name__eq='St. Petersburg')

    # RQL query = eq(address.city.name,St. Petersburg)


Q-expressions supports logic operators.

* \| - or
* & - and
* ~ invert

:: 

    from trood.api.custodian.records.query import Q


    client.records.query('person').filter((Q(age__gt=18) | Q(age__lt=53)) & Q(is_active__eq=True))
    # RQL query = and(or(gt(age,18),lt(age,53)),eq(is_active,True))

    client.records.query('person').filter((Q(age__gt=18) | Q(age__lt=53)) & Q(is_active__eq=True)) \
        .filter(address__city__name__eq='St. Petersburg')
    # RQL quey = and(and(or(gt(age,18),lt(age,53)),eq(is_active,True)),eq(address.city.name,St. Petersburg))

    client.records.query('person').filter((Q(age__gt=18) | Q(age__lt=53)) & ~Q(is_active__eq=True))
    # RQL query = and(or(gt(age,18),lt(age,53)),not(eq(is_active,True)))

Sort.
::

    client.records.query('person').filter(is_active__eq=True).order_by('+person__last_name', '-person__phone_number')
    #   RQL query = eq(is_active,True),sort(+person.last_name, -person.phone_number)


Limit, offset.
::

    q = client.records.query('person').filter(is_active__eq=True)[150:200]
    # RQL query = eq(is_active,True),limit(150,50)