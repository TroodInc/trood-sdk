from trood.api.custodian.command import Command, COMMAND_METHOD
from trood.api.custodian.exceptions import CommandExecutionFailureException, RecordAlreadyExistsException, ObjectUpdateException, \
    RecordUpdateException, CasFailureException, ObjectDeletionException
from trood.api.custodian.records.model import Record
from trood.api.custodian.records.query import Query


class RecordsManager:
    def __init__(self, client):
        self.client = client

    def _get_record_command_name(self, obj_name, record_id=None) -> str:
        """
        Constructs an uri chunk for API communication
        :param obj:
        :param record_id:
        :return:
        """
        args = ['data', obj_name]
        if record_id:
            args.append(str(record_id))
        return '/'.join(args)

    def partial_update(self, obj_name: str, pk, values, **kwargs):
        """
        Performs partial update of existing record
        :param obj_name:        
        """
        data, ok = self.client.execute(
            command=Command(name=self._get_record_command_name(obj_name, pk),
                            method=COMMAND_METHOD.PATCH),
            data=values,
            params=kwargs
        )
        if ok:
            return Record(obj_name, **data)
        else:
            if data.get('code') == 'cas_failed':
                raise CasFailureException(data.get('Msg', ''))
            else:
                raise RecordUpdateException(data.get('Msg', ''))

    def get(self, obj_name: str, record_id: str, **kwargs):
        """
        Retrieves an existing record from Custodian
        :param obj_name:
        :param record_id:
        """
        data, ok = self.client.execute(
            command=Command(name=self._get_record_command_name(obj_name, record_id), method=COMMAND_METHOD.GET),
            params=kwargs
        )
        return Record(obj_name, **data) if ok else None

    def _query(self, obj_name: str, query_string: str, **kwargs):
        """
        Performs an Custodian API call and returns a list of records
        :param obj_name:
        :param query_string:
        """
        if kwargs.get("omit_outers", None) is False:
            del kwargs['omit_outers']
        data, _ = self.client.execute(
            command=Command(name=self._get_record_command_name(obj_name), method=COMMAND_METHOD.GET),
            params={'q': query_string, **kwargs}
        )

        records = []
        for record_data in data:
            records.append(Record(obj_name, **record_data))
        return records

    def query(self, obj_name: str, depth=1, omit_outers=False) -> Query:
        """
        Returns a Query object
        :param obj_name:
        :return:
        """
        return Query(obj_name, self, depth=depth, omit_outers=omit_outers)

    def create(self, *records: Record, **kwargs):
        """
        Creates new records in the Custodian.
        :param records:
        """
        requests_data = self._get_request_data(*records)
        self._check_records_have_same_object(*records)
        obj = records[0].obj
        data, ok = self.client.execute(
            command=Command(name=self._get_record_command_name(obj), method=COMMAND_METHOD.POST),
            data=requests_data, params=kwargs
        )
        records = []
        if ok:
            if isinstance(data, dict):
                return Record(obj, **data)

            elif isinstance(data, list):
                return [Record(obj, **d) for d in data]

        elif data.get('Msg', '').find('duplicate') != -1:
            raise RecordAlreadyExistsException
        else:
            raise CommandExecutionFailureException(data.get('Msg'))

    def update(self, *records: Record, **kwargs):
        """
        Updates new records in the Custodian.
        :param records:
        """
        self._check_records_have_same_object(*records)
        obj = records[0].obj
        data, ok = self.client.execute(
            command=Command(name=self._get_record_command_name(obj), method=COMMAND_METHOD.PATCH),
            data=[record.data for record in records], params=kwargs
        )

        if ok:
            for i, d in enumerate(data):
                print(d)
                records[i].__init__(obj, **d)
            if len(records) == 1:
                return records[0]
            return list(records)
        
        else:
            raise ObjectUpdateException(data.get('Msg'))

    def delete(self, *records: Record):
        """
        Deletes records from the Custodian.
        :param records:
        """
        if records:
            self._check_records_have_same_object(*records)
            obj = records[0].obj
            data, ok = self.client.execute(
                command=Command(name=self._get_record_command_name(obj), method=COMMAND_METHOD.DELETE),
                data=[{"id": record.get_pk()} for record in records]
            )
            if ok:
                for record in records:
                    record.id = None
                if len(records) == 1:
                    return records[0]
                return list(records)
            else:
                raise ObjectDeletionException(data.get('Msg'))
        else:
            return []
            
    def _check_records_have_same_object(self, *records: Record):
        """
        Bulk operations are permitted only for one object at time
        :param records:
        :return:
        """
        obj = records[0].obj
        for record in records[1:]:
            assert obj == record.obj, 'Attempted to perform bulk operation on the list of diverse records'
        return True

    def _get_request_data(self, *records):
        if len(records) == 1:
            return records[0].data
        else:
            return [record.data for record in records]
