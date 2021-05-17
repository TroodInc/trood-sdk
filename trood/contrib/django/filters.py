from functools import reduce
from operator import __or__, __and__, __invert__

from django.conf import settings

from django.db.models import Q, Field, Lookup
from pyparsing import *
from rest_framework.filters import BaseFilterBackend
from rest_framework import exceptions


@Field.register_lookup
class Not(Lookup):
    lookup_name = 'not'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        return "%s <> %s ESCAPE '\\'" % (lhs, rhs), params


@Field.register_lookup
class Like(Lookup):
    lookup_name = 'like'

    def as_sql(self, compiler, connection):
        lhs, lhs_params = self.process_lhs(compiler, connection)
        rhs, rhs_params = self.process_rhs(compiler, connection)
        params = lhs_params + rhs_params
        if self.rhs_is_direct_value() and params and not self.bilateral_transforms:
            params[0] = params[0].replace('*', '%')
        return "%s ILIKE %s ESCAPE '\\'" % (lhs, rhs), params


class TroodRQLFilterBackend(BaseFilterBackend):
    """
    Filter that uses a RQL query.

    The RQL query is expected to be passed as a querystring parameter.
    The RQL_FILTER_QUERY_PARAM setting (which defaults to 'rql') specifies the
    name of the querystring parameter used.
    """

    AND = Literal('and').setParseAction(lambda: 'AND')
    OR = Literal('or').setParseAction(lambda: 'OR')
    NOT = Literal('not').setParseAction(lambda: 'NOT')

    EQ = Literal('eq').setParseAction(lambda: 'exact')
    NE = Literal('ne').setParseAction(lambda: 'ne')
    GE = Literal('ge').setParseAction(lambda: 'gte')
    GT = Literal('gt').setParseAction(lambda: 'gt')
    LE = Literal('le').setParseAction(lambda: 'lte')
    LT = Literal('lt').setParseAction(lambda: 'lt')
    IN = Literal('in').setParseAction(lambda: 'in')
    LIKE = Literal('like').setParseAction(lambda: 'like')

    FN = EQ | NE | GE | GT | LE | LT | IN | LIKE

    OB = Literal('(').suppress()
    CB = Literal(')').suppress()
    CM = Literal(',').suppress()

    TRUE = CaselessKeyword('True') + Optional(OB + CB)
    FALSE = CaselessKeyword('False') + Optional(OB + CB)

    BOOL = TRUE.setParseAction(lambda: True) | FALSE.setParseAction(lambda: False)

    NAME = Word(alphas + '_.', alphanums + '_.')
    VALUE = Word(alphanums + ' _.*+-:') | Literal('"').suppress() + Word(alphanums + ' _.*') + Literal('"').suppress()

    ARRAY = OB + delimitedList(VALUE, ',') + CB
    ARRAY = ARRAY.setParseAction(lambda s, loc, toks: [toks])

    SIMPLE_COND = FN + OB + NAME + CM + (BOOL | VALUE | ARRAY) + CB

    NESTED_CONDS = Forward()
    AGGREGATE = (AND | OR | NOT) + OB + delimitedList(NESTED_CONDS, ',') + CB
    COND = Group(SIMPLE_COND) | Group(AGGREGATE)
    NESTED_CONDS << COND

    QUERY = NESTED_CONDS

    query_param = getattr(settings, 'RQL_FILTER_QUERY_PARAM', 'rql')

    @classmethod
    def parse_rql(cls, rql):
        scan = list(cls.QUERY.scanString(rql))
        if len(scan) > 1:
            part_rql = rql[scan[0][1]:scan[-1][2]]
            rql = rql.replace(part_rql, f'and({part_rql})')
        try:
            parse_results = cls.QUERY.parseString(rql)
        except ParseException:
            return []
        return parse_results.asList()

    @classmethod
    def make_query(cls, data):
        conditions = []
        for fn in data:
            if fn[0] == 'AND':
                res = cls.make_query(fn[1:])
                conditions.append(reduce(__and__, res) if res else [])
            elif fn[0] == 'OR':
                res = cls.make_query(fn[1:])
                conditions.append(reduce(__or__, res) if res else [])
            elif fn[0] == 'NOT':
                res = cls.make_query(fn[1:])
                conditions.append(__invert__(res[0]) if res else [])
            else:
                field = '{}__{}'.format(fn[1].replace('.', '__'), fn[0])
                conditions.append(Q(**{field: convert_numeric(fn[2])}))
        return conditions

    @classmethod
    def get_ordering(cls, data):
        parsed = re.search('sort\(([^\)]+)\)', data)
        if parsed:
            parts = parsed.group(1).replace('+', '').split(',')
            return list(map(lambda a: a.strip(), parts))

        return []

    def filter_queryset(self, request, queryset, view):
        qs = queryset

        if self.query_param in request.GET:
            query_string = ','.join(request.GET.getlist(self.query_param, []))

            if len(query_string):
                condition = self.make_query(self.parse_rql(query_string))

                qs = qs.filter(*condition)

                ordering = self.get_ordering(query_string)

                qs = qs.order_by(*ordering)

        return qs.distinct()


def convert_numeric(val):
    if type(val) is str:
        if val.isnumeric():
            if '.' in val:
                val = float(val)
            else:
                val = int(val)
    elif type(val) is list:
        for i, a in enumerate(val):
            val[i] = convert_numeric(a)

    return val
