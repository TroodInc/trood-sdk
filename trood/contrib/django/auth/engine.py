from operator import __or__
from functools import reduce

from django.conf import settings
from django.db.models import Q
from rest_framework.exceptions import PermissionDenied

from trood.core.utils import get_attribute_path


class TroodABACResource(object):

    def __init__(self, name=None):
        self.name = name

    def __call__(self,  obj):
        setattr(obj, "_is_abac", True)

        if self.name:
            setattr(obj, "_abac_resource", self.name)
        else:
            setattr(obj, "_abac_resource", obj.__name__)

        return obj


class TroodABACEngine:
    filters = []
    mask = []

    def __init__(self, rules=None):
        self.rules = rules

    def check_permited(self, request, view):
        paths = [f"{view.basename}.{view.action}", f"{view.basename}.*", f"*.{view.action}", "*.*"]
        rules = []
        for p in paths:
            rules.extend(
                get_attribute_path(self.rules, settings.SERVICE_DOMAIN + "." + p, default=[])
            )

        resolver = TroodABACResolver(subject=request.user, context=request.data)

        for rule in rules:
            passed, result, filters = resolver.evaluate_rule(rule)
            if passed and result == 'allow':
                self.filters = filters
                self.mask = rule.get('mask')
                return True
            elif passed and result == 'deny':
                raise PermissionDenied("Access restricted by ABAC access rule")

        if get_attribute_path(self.rules, settings.SERVICE_DOMAIN + "._default_resolution") == 'allow' \
                or get_attribute_path(self.rules, "_default_resolution") == 'allow':
            return True

        raise PermissionDenied("Access restricted by ABAC access rule")

    def filter_data(self, data):
        return data.filter(*self.filters)


class TroodABACResolver:

    def __init__(self, subject={}, context={}):
        self.data_source = {
            "sbj": subject,
            "ctx": context
        }

    def evaluate_rule(self, rule: dict) -> (bool, str, list):
        passed, filters = self.evaluate_condition(rule['rule'])

        return passed, rule['result'], filters

    def evaluate_condition(self, condition):
        filters = []
        result = True
        operator = "exact"

        for operand, value in condition.items():
            if type(value) is dict:
                operator, value = list(value.items())[0]

            elif type(value) is list:
                operator = operand

            operand, value, is_filter = self.reveal(operand, value)

            if is_filter:
                filters.append(self.make_filter(operand, value))
            else:
                res, flt = getattr(self, f'operator_{operator}')(value, operand)
                if flt:
                    filters.append(flt)

                if not res:
                    result = False

        return result, filters

    def make_filter(self, operand: str, value):
        operator = "exact"
        if type(value) is dict:
            operator, value = list(value.items())[0]

        operand = "{}__{}".format(operand.replace(".", "__"), operator)

        return Q(**{operand: value})

    def reveal(self, operand: str, value):
        is_filter = False
        parts = operand.split('.', 1)

        if len(parts) == 2:
            if parts[0] in self.data_source:
                operand = get_attribute_path(self.data_source[parts[0]], parts[1])
            elif parts[0] == 'obj':
                operand = parts[1]
                is_filter = True

        if type(value) is str:
            parts = value.split('.', 1)
            if len(parts) == 2 and parts[0] != 'obj' and parts[0] in self.data_source:
                value = get_attribute_path(self.data_source[parts[0]], parts[1])

        return operand, value, is_filter

    def operator_exact(self, value, operand):
        return operand == value, []

    def operator_not(self, value, operand):
        return operand != value, []

    def operator_in(self, value, operand):
        return operand in value, []

    def operator_lt(self, value, operand):
        return operand < value, []

    def operator_gt(self, value, operand):
        return operand > value, []

    def operator_and(self, conditions: list, *args) -> (bool, list):
        filters = []

        for condition in conditions:
            res, flt = self.evaluate_condition(condition)
            filters.extend(flt)

            if not res:
                return False, []

        return True, filters

    def operator_or(self, conditions: list, *args) -> (bool, list):
        filters = []

        result = False
        for condition in conditions:
            res, flt = self.evaluate_condition(condition)

            if flt:
                filters.extend(flt)

            if res:
                result = True

        return result, reduce(__or__, filters) if filters else []
