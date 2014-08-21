import datetime as dt
from decimal import Decimal as D

from blazeutils.testing import raises
import formencode
from .helpers import query_to_str

from webgrid.filters import OptionsFilterBase, TextFilter, IntFilter, NumberFilter, DateFilter, \
    DateTimeFilter
from webgrid_ta.model.entities import Person, db

from .helpers import ModelBase


class CheckFilterBase(ModelBase):

    def assert_in_query(self, query, test_for):
        query_str = query_to_str(query)
        assert test_for in query_str, '{} not found in {}'.format(test_for, query_str)

    def assert_filter_query(self, filter, test_for):
        query = filter.apply(db.session.query(Person.id))
        self.assert_in_query(query, test_for)

class TestTextFilter(CheckFilterBase):

    def test_eq(self):
        tf = TextFilter(Person.firstname)
        tf.set('eq', 'foo')
        query = tf.apply(db.session.query(Person.id))
        self.assert_in_query(query, "WHERE persons.firstname = 'foo'")

    def test_not_eq(self):
        tf = TextFilter(Person.firstname)
        tf.set('!eq', 'foo')
        query = tf.apply(db.session.query(Person.id))
        self.assert_in_query(query, "WHERE persons.firstname != 'foo'")

    def test_empty(self):
        tf = TextFilter(Person.firstname)
        tf.set('empty', 'foo')
        query = tf.apply(db.session.query(Person.id))
        self.assert_in_query(query, "WHERE persons.firstname IS NULL OR persons.firstname = ''")

    def test_not_empty(self):
        tf = TextFilter(Person.firstname)
        tf.set('!empty', 'foo')
        query = tf.apply(db.session.query(Person.id))
        self.assert_in_query(query, "WHERE persons.firstname IS NOT NULL AND persons.firstname != ''")

    def test_contains(self):
        tf = TextFilter(Person.firstname)
        tf.set('contains', 'foo')
        query = tf.apply(db.session.query(Person.id))
        self.assert_in_query(query, "WHERE persons.firstname LIKE '%foo%'")

    def test_doesnt_contain(self):
        tf = TextFilter(Person.firstname)
        tf.set('!contains', 'foo')
        query = tf.apply(db.session.query(Person.id))
        self.assert_in_query(query, "WHERE persons.firstname NOT LIKE '%foo%'")

class TestNumberFilters(CheckFilterBase):
    """
        Testing IntFilter mostly because the other classes inherit from the same base,
        but make sure we test value typing for each.

        Also, most of the operators are inherited, so only testing the ones
        that are specific to number filters.
    """

    def test_int_eq(self):
        filter = IntFilter(Person.numericcol)
        filter.set('eq', '1')
        self.assert_filter_query(filter, "WHERE persons.numericcol = 1")

    def test_int_lte(self):
        filter = IntFilter(Person.numericcol)
        filter.set('lte', '1')
        self.assert_filter_query(filter, "WHERE persons.numericcol <= 1")

    def test_int_gte(self):
        filter = IntFilter(Person.numericcol)
        filter.set('gte', '1')
        self.assert_filter_query(filter, "WHERE persons.numericcol >= 1")

    def test_number_filter_type_conversion1(self):
        filter = NumberFilter(Person.numericcol)
        filter.set('eq', '1')
        self.assert_filter_query(filter, "WHERE persons.numericcol = 1")

    def test_number_filter_type_conversion2(self):
        filter = NumberFilter(Person.numericcol)
        filter.set('eq', '1.5')
        self.assert_filter_query(filter, "WHERE persons.numericcol = 1.5")

    @raises(formencode.Invalid, 'Please enter an integer value')
    def test_int_invalid(self):
        filter = IntFilter(Person.numericcol)
        filter.set('eq', 'a')

    @raises(formencode.Invalid, 'Please enter a number')
    def test_number_invalid(self):
        filter = NumberFilter(Person.numericcol)
        filter.set('eq', 'a')

    @raises(formencode.Invalid, 'Please enter a value')
    def test_number_lte_null(self):
        filter = NumberFilter(Person.numericcol)
        filter.set('lte', None)

    @raises(formencode.Invalid, 'Please enter a value')
    def test_number_gte_null(self):
        filter = NumberFilter(Person.numericcol)
        filter.set('gte', None)

    @raises(formencode.Invalid, 'Please enter a value')
    def test_number_eq_null(self):
        filter = NumberFilter(Person.numericcol)
        filter.set('eq', None)

    @raises(formencode.Invalid, 'Please enter a value')
    def test_number_neq_null(self):
        filter = NumberFilter(Person.numericcol)
        filter.set('!eq', None)

    def test_number_empty(self):
        filter = NumberFilter(Person.numericcol)
        filter.set('empty', '')

    def test_number_not_empty(self):
        filter = NumberFilter(Person.numericcol)
        filter.set('!empty', '')


class TestDateFilter(CheckFilterBase):

    def test_eq(self):
        filter = DateFilter(Person.due_date)
        filter.set('eq', '12/31/2010')
        self.assert_filter_query(filter, "WHERE persons.due_date = '2010-12-31'")

    def test_not_eq(self):
        filter = DateFilter(Person.due_date)
        filter.set('!eq', '12/31/2010')
        self.assert_filter_query(filter, "WHERE persons.due_date != '2010-12-31'")

    def test_lte(self):
        filter = DateFilter(Person.due_date)
        filter.set('lte', '12/31/2010')
        self.assert_filter_query(filter, "WHERE persons.due_date <= '2010-12-31'")

    def test_gte(self):
        filter = DateFilter(Person.due_date)
        filter.set('gte', '12/31/2010')
        self.assert_filter_query(filter, "WHERE persons.due_date >= '2010-12-31'")

    def test_empty(self):
        filter = DateFilter(Person.due_date)
        filter.set('empty', None)
        self.assert_filter_query(filter, "WHERE persons.due_date IS NULL")

    def test_not_empty(self):
        filter = DateFilter(Person.due_date)
        filter.set('!empty', None)
        self.assert_filter_query(filter, "WHERE persons.due_date IS NOT NULL")

    def test_between(self):
        filter = DateFilter(Person.due_date)
        filter.set('between', '1/31/2010', '12/31/2010')
        self.assert_filter_query(filter, "WHERE persons.due_date BETWEEN '2010-01-31' AND '2010-12-31'")

    def test_between_swap(self):
        filter = DateFilter(Person.due_date)
        filter.set('between', '12/31/2010', '1/31/2010')
        self.assert_filter_query(filter, "WHERE persons.due_date BETWEEN '2010-01-31' AND '2010-12-31'")

    def test_not_between(self):
        filter = DateFilter(Person.due_date)
        filter.set('!between', '1/31/2010', '12/31/2010')
        self.assert_filter_query(filter, "WHERE persons.due_date NOT BETWEEN '2010-01-31' AND '2010-12-31'")

    def test_days_ago(self):
        filter = DateFilter(Person.due_date, _now=dt.date(2012,1,1))
        filter.set('da', '10')
        self.assert_filter_query(filter, "WHERE persons.due_date = '2011-12-22'")

    def test_less_than_days_ago(self):
        filter = DateFilter(Person.due_date, _now=dt.date(2012,1,1))
        filter.set('ltda', '10')
        self.assert_filter_query(filter, "WHERE persons.due_date > '2011-12-22' AND persons.due_date < '2012-01-01'")

    def test_more_than_days_ago(self):
        filter = DateFilter(Person.due_date, _now=dt.date(2012,1,1))
        filter.set('mtda', '10')
        self.assert_filter_query(filter, "WHERE persons.due_date < '2011-12-22'")

    def test_in_less_than_days(self):
        filter = DateFilter(Person.due_date, _now=dt.date(2012,1,1))
        filter.set('iltd', '10')
        self.assert_filter_query(filter, "WHERE persons.due_date >= '2012-01-01' AND persons.due_date < '2012-01-11'")

    def test_in_more_than_days(self):
        filter = DateFilter(Person.due_date, _now=dt.date(2012,1,1))
        filter.set('imtd', '10')
        self.assert_filter_query(filter, "WHERE persons.due_date > '2012-01-11'")

    def test_in_days(self):
        filter = DateFilter(Person.due_date, _now=dt.date(2012,1,1))
        filter.set('ind', '10')
        self.assert_filter_query(filter, "WHERE persons.due_date = '2012-01-11'")

    def test_today(self):
        filter = DateFilter(Person.due_date, _now=dt.date(2012,1,1))
        filter.set('today', None)
        self.assert_filter_query(filter, "WHERE persons.due_date = '2012-01-01'")

    def test_this_week(self):
        filter = DateFilter(Person.due_date, _now=dt.date(2012,1,4))
        filter.set('thisweek', None)
        self.assert_filter_query(filter, "WHERE persons.due_date BETWEEN '2012-01-01' AND '2012-01-07'")

    def test_this_week_left_edge(self):
        filter = DateFilter(Person.due_date, _now=dt.date(2012,1,1))
        filter.set('thisweek', None)
        self.assert_filter_query(filter, "WHERE persons.due_date BETWEEN '2012-01-01' AND '2012-01-07'")

    def test_this_week_right_edge(self):
        filter = DateFilter(Person.due_date, _now=dt.date(2012,1,7))
        filter.set('thisweek', None)
        self.assert_filter_query(filter, "WHERE persons.due_date BETWEEN '2012-01-01' AND '2012-01-07'")

    @raises(formencode.Invalid, 'invalid date')
    def test_invalid_date(self):
        filter = DateFilter(Person.due_date)
        filter.set('eq', '7/45/2007')

    @raises(formencode.Invalid, 'invalid date (parsing exception)')
    def test_parser_error(self):
        # can probably be removed if this ever gets fixed:
        # https://bugs.launchpad.net/dateutil/+bug/1257985
        filter = DateFilter(Person.due_date)
        filter.set('eq', 'samwise gamgee')

    @raises(formencode.Invalid, 'Please enter a value')
    def test_days_operator_with_blank_value(self):
        filter = DateFilter(Person.due_date, _now=dt.date(2012,1,1))
        filter.set('ind', '')

    @raises(formencode.Invalid, 'Please enter an integer value')
    def test_days_operator_with_invalid_value(self):
        filter = DateFilter(Person.due_date, _now=dt.date(2012,1,1))
        filter.set('ind', 'a')


class TestDateTimeFilter(CheckFilterBase):

    def test_eq(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('eq', '12/31/2010')
        self.assert_filter_query(filter, "WHERE persons.createdts BETWEEN '2010-12-31 00:00:00.000000' AND '2010-12-31 23:59:59.999999'")

    def test_eq_with_time(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('eq', '12/31/2010 10:26:27')
        self.assert_filter_query(filter, "WHERE persons.createdts = '2010-12-31 10:26:27.000000'")

    def test_not_eq(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('!eq', '12/31/2010')
        self.assert_filter_query(filter, "WHERE persons.createdts NOT BETWEEN '2010-12-31 00:00:00.000000' AND '2010-12-31 23:59:59.999999'")

    def test_not_eq_with_time(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('!eq', '12/31/2010 10:26:27')
        self.assert_filter_query(filter, "WHERE persons.createdts != '2010-12-31 10:26:27.000000'")

    def test_lte(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('lte', '12/31/2010')
        self.assert_filter_query(filter, "WHERE persons.createdts <= '2010-12-31 23:59:59.999999'")

    def test_lte_with_time(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('lte', '12/31/2010 12:00')
        self.assert_filter_query(filter, "WHERE persons.createdts <= '2010-12-31 12:00:00.000000'")

    def test_gte(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('gte', '12/31/2010')
        self.assert_filter_query(filter, "WHERE persons.createdts >= '2010-12-31 00:00:00.000000'")

    def test_gte_with_time(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('gte', '12/31/2010 12:35')
        self.assert_filter_query(filter, "WHERE persons.createdts >= '2010-12-31 12:35:00.000000'")

    def test_empty(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('empty', None)
        self.assert_filter_query(filter, "WHERE persons.createdts IS NULL")

    def test_not_empty(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('!empty', None)
        self.assert_filter_query(filter, "WHERE persons.createdts IS NOT NULL")

    def test_between(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('between', '1/31/2010', '12/31/2010')
        self.assert_filter_query(filter, "WHERE persons.createdts BETWEEN '2010-01-31 00:00:00.000000' AND '2010-12-31 23:59:59.999999'")

    def test_between_with_time(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('between', '1/31/2010 10:00', '12/31/2010 10:59:59')
        self.assert_filter_query(filter, "WHERE persons.createdts BETWEEN '2010-01-31 10:00:00.000000' AND '2010-12-31 10:59:59.000000'")

    def test_between_with_explicit_midnight(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('between', '1/31/2010 10:00', '12/31/2010 00:00')
        self.assert_filter_query(filter, "WHERE persons.createdts BETWEEN '2010-01-31 10:00:00.000000' AND '2010-12-31 00:00:00.000000'")

    def test_not_between(self):
        filter = DateTimeFilter(Person.createdts)
        filter.set('!between', '1/31/2010', '12/31/2010')
        self.assert_filter_query(filter, "WHERE persons.createdts NOT BETWEEN '2010-01-31 00:00:00.000000' AND '2010-12-31 23:59:59.999999'")

    def test_days_ago(self):
        filter = DateTimeFilter(Person.createdts, _now=dt.date(2012,1,1))
        filter.set('da', '10')
        self.assert_filter_query(filter, "WHERE persons.createdts BETWEEN '2011-12-22 00:00:00.000000' AND '2011-12-22 23:59:59.999999'")

    def test_less_than_days_ago(self):
        filter = DateTimeFilter(Person.createdts, _now=dt.date(2012,1,1))
        filter.set('ltda', '10')
        self.assert_filter_query(filter, "WHERE persons.createdts > '2011-12-22 23:59:59.999999' AND persons.createdts < '2012-01-01 00:00:00.000000'")

    def test_more_than_days_ago(self):
        filter = DateTimeFilter(Person.createdts, _now=dt.date(2012,1,1))
        filter.set('mtda', '10')
        self.assert_filter_query(filter, "WHERE persons.createdts < '2011-12-22 00:00:00.000000'")

    def test_in_less_than_days(self):
        filter = DateTimeFilter(Person.createdts, _now=dt.datetime(2012,1,1,12,35))
        filter.set('iltd', '10')
        self.assert_filter_query(filter, "WHERE persons.createdts >= '2012-01-01 12:35:00.000000' AND persons.createdts < '2012-01-11 00:00:00.000000'")

    def test_in_more_than_days(self):
        filter = DateTimeFilter(Person.createdts, _now=dt.datetime(2012,1,1,12,35))
        filter.set('imtd', '10')
        self.assert_filter_query(filter, "WHERE persons.createdts > '2012-01-11 23:59:59.999999'")

    def test_in_days(self):
        filter = DateTimeFilter(Person.createdts, _now=dt.datetime(2012,1,1,12,35))
        filter.set('ind', '10')
        self.assert_filter_query(filter, "WHERE persons.createdts BETWEEN '2012-01-11 00:00:00.000000' AND '2012-01-11 23:59:59.999999'")

    def test_today(self):
        filter = DateTimeFilter(Person.createdts, _now=dt.datetime(2012,1,1,12,35))
        filter.set('today', None)
        self.assert_filter_query(filter, "WHERE persons.createdts BETWEEN '2012-01-01 00:00:00.000000' AND '2012-01-01 23:59:59.999999'")

    def test_this_week(self):
        filter = DateTimeFilter(Person.createdts, _now=dt.datetime(2012,1,4,12,35))
        filter.set('thisweek', None)
        self.assert_filter_query(filter, "WHERE persons.createdts BETWEEN '2012-01-01 00:00:00.000000' AND '2012-01-07 23:59:59.999999'")

    def test_this_week_left_edge(self):
        filter = DateTimeFilter(Person.createdts, _now=dt.datetime(2012,1,1))
        filter.set('thisweek', None)
        self.assert_filter_query(filter, "WHERE persons.createdts BETWEEN '2012-01-01 00:00:00.000000' AND '2012-01-07 23:59:59.999999'")

    def test_this_week_right_edge(self):
        filter = DateTimeFilter(Person.createdts, _now=dt.datetime(2012,1,1,23,59,59,999999))
        filter.set('thisweek', None)
        self.assert_filter_query(filter, "WHERE persons.createdts BETWEEN '2012-01-01 00:00:00.000000' AND '2012-01-07 23:59:59.999999'")

    @raises(formencode.Invalid, 'invalid date (parsing exception)')
    def test_parser_error(self):
        # can probably be removed if this ever gets fixed:
        # https://bugs.launchpad.net/dateutil/+bug/1257985
        filter = DateTimeFilter(Person.createdts)
        filter.set('eq', 'samwise gamgee')

    @raises(formencode.Invalid, 'Please enter a value')
    def test_days_operator_with_empty_value(self):
        filter = DateTimeFilter(Person.createdts, _now=dt.datetime(2012,1,1,12,35))
        filter.set('ind', '')

    def test_set_makes_op_none(self):
        filter = DateTimeFilter(Person.createdts, _now=dt.datetime(2012,1,1,12,35))
        filter.op = 'foo'
        filter.set('', '')
        assert filter.op is None


class StateFilter(OptionsFilterBase):
    options_from = (('in', 'IN'), ('ky', 'KY'))


class SortOrderFilter(OptionsFilterBase):
    options_from = ((1, 'One'), (2, 'Two'))


class FloatFilter(OptionsFilterBase):
    options_from = ((1.1, '1.1'), (2.2, '2.2'))


class DecimalFilter(OptionsFilterBase):
    options_from = ((D('1.1'), '1.1'), (D('2.2'), '2.2'))


class BoolFilter(OptionsFilterBase):
    options_from = ((1, 'True'), (0, 'False'))


class BadTypeFilter(OptionsFilterBase):
    options_from = (([], 'Empty List'),)


class TestOptionsFilter(CheckFilterBase):

    def test_is(self):
        filter = StateFilter(Person.state).new_instance()
        # the "foo" should get filtered out
        filter.set('is', ['in', 'foo'])
        self.assert_filter_query(filter, "WHERE persons.state = 'in'")

    def test_is_multiple(self):
        filter = StateFilter(Person.state).new_instance()
        filter.set('is', ['in', 'ky'])
        self.assert_filter_query(filter, "WHERE persons.state IN ('in', 'ky')")

    def test_is_not(self):
        filter = StateFilter(Person.state).new_instance()
        filter.set('!is', ['in'])
        self.assert_filter_query(filter, "WHERE persons.state != 'in'")

    def test_is_not_multiple(self):
        filter = StateFilter(Person.state).new_instance()
        filter.set('!is', ['in', 'ky'])
        self.assert_filter_query(filter, "WHERE persons.state NOT IN ('in', 'ky')")

    def test_empty(self):
        filter = StateFilter(Person.state).new_instance()
        filter.set('empty', None)
        self.assert_filter_query(filter, "WHERE persons.state IS NULL")

    def test_not_empty(self):
        filter = StateFilter(Person.state).new_instance()
        filter.set('!empty', None)
        self.assert_filter_query(filter, "WHERE persons.state IS NOT NULL")

    def test_integer_conversion(self):
        filter = SortOrderFilter(Person.sortorder).new_instance()
        # the '3' should get filtered out because its not a valid option
        # the 'foo' should get filtered out because its the wrong type (and isn't an option)
        filter.set('is', ['1', '2', '3', 'foo'])
        self.assert_filter_query(filter, "WHERE persons.sortorder IN (1, 2)")

    def test_float_conversion(self):
        filter = FloatFilter(Person.floatcol).new_instance()
        filter.set('is', ['1.1'])
        self.assert_filter_query(filter, "WHERE persons.floatcol = 1.1")

    def test_decimal_conversion(self):
        filter = DecimalFilter(Person.numericcol).new_instance()
        filter.set('is', ['1.1'])
        self.assert_filter_query(filter, "WHERE persons.numericcol = 1.1")

    def test_custom_validator(self):
        filter = BoolFilter(Person.boolcol, lambda x: 1 if x == '1' else 0).new_instance()
        filter.set('is', ['1'])
        self.assert_filter_query(filter, "WHERE persons.boolcol = 1")

    @raises(TypeError, "can't use value_modifier='auto' when option keys are <type 'list'>")
    def test_unkonwn_type(self):
        filter = BadTypeFilter(Person.boolcol).new_instance()

    def test_value_not_in_options_makes_inactive(self):
        filter = StateFilter(Person.state).new_instance()

        filter.set('is', ['foo'])
        assert not filter.is_active

        filter.set('!is', ['foo'])
        assert not filter.is_active

    @raises(ValueError, 'value_modifier argument set to "auto", but the options set is empty and the type can therefore not be determined')
    def test_auto_validation_with_no_options(self):
        class NoOptionsFilter(OptionsFilterBase):
            pass
        filter = NoOptionsFilter(Person.numericcol).new_instance()

    @raises(TypeError, 'value_modifier must be the string "auto", have a "to_python" attribute, or be a callable')
    def test_modifier_wrong_type(self):
        filter = StateFilter(Person.state, value_modifier=1).new_instance()
