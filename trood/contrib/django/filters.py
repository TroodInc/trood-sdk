import logging
import re
from functools import reduce
from operator import __or__, __and__

from django.conf import settings

from django.db.models import Q
from pyparsing import Literal, Word, alphas, alphanums, Group, Forward, delimitedList, ParseException
from rest_framework.filters import BaseFilterBackend
from trood.core.converters import convert


logger = logging.getLogger(__name__)


class RQLParser:

    AND = Literal('and').setParseAction(lambda: 'AND')
    OR = Literal('or').setParseAction(lambda: 'OR')

    EQ = Literal('eq').setParseAction(lambda: 'exact')
    NE = Literal('ne').setParseAction(lambda: 'ne')
    GE = Literal('ge').setParseAction(lambda: 'gte')
    GT = Literal('gt').setParseAction(lambda: 'gt')
    LE = Literal('le').setParseAction(lambda: 'lte')
    LT = Literal('lt').setParseAction(lambda: 'lt')
    IN = Literal('in').setParseAction(lambda: 'in')
    LIKE = Literal('icontains').setParseAction(lambda: 'like')

    FN = EQ | NE | GE | GT | LE | LT | IN | LIKE

    OB = Literal('(').suppress()
    CB = Literal(')').suppress()
    CM = Literal(',').suppress()

    NAME = Word(alphas + '_.', alphanums + '_.')
    VALUE = Word(alphanums + '_.') | Literal('"').suppress() + Word(alphanums + '_.') + Literal('"').suppress()

    ARRAY = OB + delimitedList(VALUE, ',') + CB
    ARRAY = ARRAY.setParseAction(lambda s, loc, toks: [toks])

    SIMPLE_COND = FN + OB + NAME + CM + (VALUE | ARRAY) + CB

    NESTED_CONDS = Forward()
    AGGREGATE = (AND | OR) + OB + delimitedList(NESTED_CONDS, ',') + CB
    COND = Group(SIMPLE_COND) | Group(AGGREGATE)
    NESTED_CONDS << COND

    QUERY = NESTED_CONDS

    query_param = getattr(settings, 'RQL_FILTER_QUERY_PARAM', 'rql')

    @classmethod
    def parse(cls, rql):
        try:
            parse_results = cls.QUERY.parseString(rql)
        except ParseException:
            return []
        return parse_results.asList()

class TroodRQLFilterBackend(BaseFilterBackend):
    """
    Filter that uses a RQL query.

    The RQL query is expected to be passed as a querystring parameter.
    The RQL_FILTER_QUERY_PARAM setting (which defaults to 'rql') specifies the
    name of the querystring parameter used.
    """

    @classmethod
    def get_query(cls, rql_query):
        query = []
        for fn in Parser.parse(rql_query)
            if fn[0] == 'AND':
                res = cls.get_condition(fn[1:])
                query.append(reduce(__and__, res) if res else [])
            elif fn[0] == 'OR':
                res = cls.get_condition(fn[1:])
                query.append(reduce(__or__, res) if res else [])
            else:
                field = '{}__{}'.format(fn[1].replace('.', '__'), fn[0])
                query.append(Q(**{field: convert(fn[2])})))

        return query
    
    @staticmethod
    def get_ordering(rql_query):
        _key = 'sort('
        query = rql_query.split(_key)[1]
        ordering = [
            v.strip() if v.strip()[0] == '-' else v.strip()[1:]
            for v in query[1][:query.index(')')].split(',')
        ]
        return ordering

    def filter_queryset(self, request, queryset, view):
        if self.query_param not in request.GET:
            return queryset

        rql_query = request.GET.get(self.query_param, [])
        if len(query) == 0:
            return queryset

        query = self.get_query(rql_query)
        queryset = queryset.filter(*query)
        ordering = self.get_ordering(rql_query)
        queryset = queryset.order_by(*ordering)
        return queryset
