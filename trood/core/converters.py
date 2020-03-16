from abc import ABC
from collections.abc import Iterable



class BaseConverter(ABC):

    def __init__(self, value):
        self.value = value

    def convert(self):
        if type(self.value) is str:
            value = self.convert_string(self.value)
        elif isinstance(self.value, Iterable):
            value = (self.convert(v) for v in self.value)
        else:
            raise NotImplementedError

        return value

    def convert_string(self, value):
        is_digit = value.replace(".", "", 1).isdigit()
        if is_digit and "." in value:
            value = float(value)
        elif is_digit:
            value = int(value)
        elif value == "True()":
            value = True
        elif value == "False()":
            value = False

        return value


class DjangoConverter(BaseConverter):
    pass
