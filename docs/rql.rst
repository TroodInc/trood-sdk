.. _rql:

Custodian RQL documetation
==========================
Description.

Resource Query Language (RQL) is a query language designed for use in URIs.

Here is a definition of the common operators:

* and(<query>,<query>,...) - Applies all the given queries.
* or(<query>,<query>,...) - The union of the given queries.
* eq(<property>,<value>) - Filters for objects where the specified property's value is equal to the provided value.
* lt(<property>,<value>) - Filters for objects where the specified property's value is less than the provided value.
* le(<property>,<value>) - Filters for objects where the specified property's value is less than or equal to the provided value.
* gt(<property>,<value>) - Filters for objects where the specified property's value is greater than the provided value.
* ge(<property>,<value>) - Filters for objects where the specified property's value is greater than or equal to the provided value.
* ne(<property>,<value>) - Filters for objects where the specified property's value is not equal to the provided value.
* in(<property>,<array-of-values>) - Filters for objects where the specified property's value is in the provided array.
* like(<property>,<\*expression\*>) Filters for objects where the specified property's value is an array and the array contains any value that equals the provided value or satisfies the provided expression.
* limit(<offset>, <limit>) - Returns the given range of objects from the result set.
* sort(<+|-><property) - Sorts by the given property in order specified by the prefix (+ for ascending, - for descending).
* is_null(<property>,<true|false>) - Filters for objects where the specified property's value is null or not null.
* not(<operator>) - Inverts operators.

eq
---
eq(<property>,<value>) - Filters for objects where the specified property's value is equal to the provided value.

::

    GET  /custodian/data/person?rql=eq(name,Ivan)

Retrive person with name Ivan.

You can also retrive a person using several parameters.

::

    GET  /custodian/data/person?rql=eq(name,Ivan),eq(age,25)

ne
---
ne(<property>,<value>) - Filters for objects where the specified property's value is not equal to the provided value.

::

    GET  /custodian/data/person?rql=ne(name,Ivan)

Retrive person whos name is not Ivan.

in
---
in(<property>,<array-of-values>) - Filters for objects where the specified property's value is in the provided array.

::

    GET  /custodian/data/person?rql=in(id,(1,2))

Retrive person with id 1 or 2.

lt
---
lt(<property>,<value>) - Filters for objects where the specified property's value is less than the provided value.

::

    GET  /custodian/data/person?rql=lt(id,10)

Retrive person with less than 10.

gt
---
gt(<property>,<value>) - Filters for objects where the specified property's value is less than the provided value.

::

    GET  /custodian/data/person?rql=gt(id,10)

Retrive person with grater than 10.

like
----
like(<property>,<\*expression\*>) Filters for objects where the specified property's value is an array and the array contains any value that equals the provided value or satisfies the provided expression.

::

    GET /custodian/data/person?rql=like(adress,*London*)"

Retrive all persons whose adress contains London.

is_null
-------
is_null(<property>,<true|false>) - Filters for objects where the specified property's value is null or not null.

::

    GET /custodian/data/person?rql=is_null(bill,true)

Retrive all persons who has bill.

and
---
and(<query>,<query>,...) - Applies all the given queries.

::

    GET /custodian/data/person?rql=and(eq(name,Ivan),is_null(bill,true))

Retrive persons with name Ivan and having bill

or
---
or(<query>,<query>,...) - The union of the given queries.

::

    GET /custodian/data/person?rql=or(eq(id,1),eq(id,2))


sort
----
sort(<+|-><property) - Sorts by the given property in order specified by the prefix (+ for ascending, - for descending).

ascending sort

::

    GET /custodian/data/person?rql=sort(id)

descending sort

::

    GET /custodian/data/person?rql=sort(-id)


not
---
not(<operator>) - Inverts operators.

Can be used with eq, in, lt, le, ge, gt, like, is_null, and, or.

::

    # eq
    GET /custodian/data/person?rql=not(eq(id,1)))

    # in
    GET /custodian/data/person?rql=not(eq(id,(1,2)))

    # lt
    GET /custodian/data/person?rql=not(lt(id,10))

    # le
    GET /custodian/data/person?rql=not(le(id,10))

    # gt
    GET /custodian/data/person?rql=not(gt(id,10))

    # ge
    GET /custodian/data/person?rql=not(ge(id,10))

    # like
    GET /custodian/data/person?rql=not(like(name,*one*))"

    # is_null
    GET /custodian/data/person?rql=not(is_null(bill,true))
    GET /custodian/data/person?rql=not(is_null(bill,false))