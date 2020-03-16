from collections.abc import Iterable


def convert(value):
    if type(value) is str:
        value = convert_string(value)
    elif isinstance(value, Iterable):
        value = (convert(v) for v in value)
    else:
        raise NotImplementedError

    return value


def convert_string(value):
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
