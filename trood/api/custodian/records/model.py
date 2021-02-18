class Record:
    __data = None
    obj = None

    def __init__(self, obj: str,  **values):
        if self.__data is None:
            self.__data = {}
        if self.obj is None:
            self.obj = obj
        self.set_data(values)

    def __setattr__(self, key, value):
        if key in self.__class__.__dict__:
            super(Record, self).__setattr__(key, value)
        else:
            self.__data[key] = value

    def __getattr__(self, item):
        return self.__data.get(item)

    @property
    def data(self):
        return self.__data

    def __repr__(self):
        return '<Record #{} of "{}" object>'.format(self.id, self.name)

    def set_data(self, values):
        for key, value in values.items():
            setattr(self, key, value)

    def get_pk(self):
        """
        Returns the record`s primary key value
        """
        return getattr(self, "id", None)

    def exists(self):
        """
        True if the record exists in the Custodian
        :return:
        """
        return self.get_pk() is not None
