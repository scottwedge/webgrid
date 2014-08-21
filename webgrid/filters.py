import calendar
import datetime as dt
from decimal import Decimal as D
import inspect

from blazeutils.dates import ensure_date, ensure_datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta, SU
import formencode
import formencode.validators as feval
from sqlalchemy.sql import or_, and_

class UnrecognizedOperator(ValueError):
    pass

class Operator(object):
    def __init__(self, key, display, field_type, hint=None):
        self.key = key
        self.display = display
        self.field_type = field_type
        self.hint = hint

class ops(object):
    eq = Operator('eq', 'is', 'input')
    not_eq = Operator('!eq', 'is not', 'input')
    is_ = Operator('is', 'is', 'select')
    not_is = Operator('!is', 'is not', 'select')
    empty = Operator('empty', 'empty', None)
    not_empty = Operator('!empty', 'not empty', None)
    contains = Operator('contains', 'contains', 'input')
    not_contains = Operator('!contains', 'doesn\'t contain', 'input')
    less_than_equal = Operator('lte', 'less than or equal', 'input')
    greater_than_equal = Operator('gte', 'greater than or equal', 'input')
    between = Operator('between', 'between', '2inputs')
    not_between = Operator('!between', 'not between', '2inputs')
    days_ago = Operator('da', 'days ago', 'input', 'days')
    less_than_days_ago = Operator('ltda', 'less than days ago', 'input', 'days')
    more_than_days_ago = Operator('mtda', 'more than days ago', 'input', 'days')
    today = Operator('today', 'today', None)
    this_week = Operator('thisweek', 'this week', None)
    in_less_than_days = Operator('iltd', 'in less than days', 'input', 'days')
    in_more_than_days = Operator('imtd', 'in more than days', 'input', 'days')
    in_days = Operator('ind', 'in days', 'input', 'days')


class FilterBase(object):
    operators = ops.eq, ops.not_eq, ops.empty, ops.not_empty
    # if needed, specifiy the name of attributes set on the static instance of
    # this class that should get copied over to a new instance by
    # new_instance()
    init_attrs_for_instance = ()
    # current HTML renderer allows for "input", "input2", and/or "select"
    input_types = 'input',
    # does this filter take a list of values in it's set() method
    receives_list = False

    def __init__(self, sa_col, default_op=None):
        # attributes from static instance
        self.sa_col = sa_col
        self.default_op = default_op

        # attributes that will start fresh for each instance
        self.op = None
        self.value1 = None
        self.value2 = None
        self.value1_set_with = None
        self.value2_set_with = None
        self._op_keys = None
        self.error = False

    @property
    def is_active(self):
        return self.op is not None and not self.error

    @property
    def is_display_active(self):
        return self.op is not None

    @property
    def op_keys(self):
        if self._op_keys is None:
            self._op_keys = [op.key for op in self.operators]
        return self._op_keys

    def set(self, op, value1, value2=None):
        if not op:
            self.op = self.default_op
            self.using_default_op = (self.default_op is not None)
            if self.op is None:
                return

        # set values used in display first, since processing validation may
        #   raise exceptions
        self.op = feval.OneOf(self.op_keys, not_empty=True).to_python(
            op or self.default_op
        )
        self.value1_set_with = value1
        self.value2_set_with = value2
        try:
            self.value1 = self.process(value1, False)
            self.value2 = self.process(value2, True)
        except formencode.Invalid:
            self.error = True
            raise

    def raise_unrecognized_op(self):
        raise UnrecognizedOperator('unrecognized operator: {0}'.format(self.op))

    def apply(self, query):
        if self.op == 'eq':
            return query.filter(self.sa_col == self.value1)
        if self.op == '!eq':
            return query.filter(self.sa_col != self.value1)
        if self.op == 'empty':
            return query.filter(self.sa_col == None)
        if self.op == '!empty':
            return query.filter(self.sa_col != None)
        if self.op == 'lte':
            return query.filter(self.sa_col <= self.value1)
        if self.op == 'gte':
            return query.filter(self.sa_col >= self.value1)

        self.raise_unrecognized_op()

    def process(self, value, is_value2):
        """
            Process the values as given to .set(), validating and manipulating
            as needed.
        """
        return value

    def format_invalid(self, exc, col):
        return '{0}: {1}'.format(
            col.label,
            str(exc)
        )

    def new_instance(self):
        cls = self.__class__
        filter = cls(self.sa_col, default_op=self.default_op)

        # try to be smart about which attributes should get copied to the
        # new instance
        for argname in inspect.getargspec(self.__init__).args:
            if argname != 'self' and hasattr(self, argname):
                setattr(filter, argname, getattr(self, argname))

        # if we aren't smart enough, let the class define explicitly
        # attributes that need to be copied over
        for attr_name in self.init_attrs_for_instance:
            setattr(filter, attr_name, getattr(self, attr_name))

        return filter

class _NoValue(object):
    pass

class OptionsFilterBase(FilterBase):
    operators =  ops.is_, ops.not_is, ops.empty, ops.not_empty
    input_types = 'select'
    receives_list = True
    options_from = ()

    def __init__(self, sa_col, value_modifier='auto', default_op=None):
        FilterBase.__init__(self, sa_col, default_op=default_op)
        # attributes from static instance
        self.value_modifier = value_modifier

        # attributes that will start fresh for each instance
        self._options_seq = None
        self._options_keys = None

    def new_instance(self):
        filter = FilterBase.new_instance(self)
        filter.setup_validator()
        return filter

    @property
    def options_seq(self):
        if self._options_seq is None:
            try:
                self._options_seq = self.options_from()
            except TypeError, e:
                if 'is not callable' not in str(e):
                    raise
                self._options_seq = self.options_from
            if self.default_op:
                self._options_seq = [(-1,'-- All --')]+self._options_seq
        return self._options_seq

    @property
    def option_keys(self):
        if self._options_keys is None:
            self._options_keys = [k for k,v in self.options_seq]
        return self._options_keys

    def setup_validator(self):
        # make an educated guess about what type the unicode values sent in on
        # a set() operation should be converted to
        if self.value_modifier == 'auto' or self.value_modifier is None:
            if self.value_modifier and len(self.option_keys) == 0:
                raise ValueError('value_modifier argument set to "auto", but '
                    'the options set is empty and the type can therefore not '
                    'be determined')
            first_key = self.option_keys[0]
            if isinstance(first_key, basestring) or self.value_modifier is None:
                self.value_modifier = feval.UnicodeString
            # this didn't work right, so commenting out for now
            #elif isinstance(first_key, bool):
            #    self.value_modifier = formencode.compound.Any(feval.Bool, feval.StringBoolean)
            elif isinstance(first_key, int):
                self.value_modifier = feval.Int
            elif isinstance(first_key, float):
                self.value_modifier = feval.Number
            elif isinstance(first_key, D):
                self.value_modifier = feval.Wrapper(to_python=D)
            else:
                raise TypeError("can't use value_modifier='auto' when option keys are {0}".format(type(first_key)))
        else:
            # if its not the string 'auto' and its not a formencode validator, assume
            # its a callable and wrap with a formencode validator
            if not hasattr(self.value_modifier, 'to_python'):
                if not hasattr(self.value_modifier, '__call__'):
                    raise TypeError('value_modifier must be the string "auto", have a "to_python" attribute, or be a callable')
                self.value_modifier = feval.Wrapper(to_python=self.value_modifier)

    def set(self, op, values, value2=None):
        if not op and not self.default_op:
            return
        self.op = op or self.default_op
        self.using_default_op = (self.default_op is not None)
        self.value1 = []
        if values is not None:
            for v in values:
                try:
                    v = self.process(v)
                    if v is not _NoValue:
                        self.value1.append(v)
                except formencode.Invalid:
                    # A normal user should be selecting from the options given,
                    # so if we encounter an Invalid exception, we are going to
                    # assume the value is erronious and just ignore it
                    pass

        # if there are no values after processing, the operator is irrelevent
        # and should be set to None so that it is as if the filter
        # is not set.
        #
        # however, we have to test the operator first, because if it is empty
        # or !empty, then it would make sense for self.value1 to be empty.
        if self.op in ('is', '!is') and not (self.value1 or self.default_op):
            self.op = None

    def process(self, value):
        if self.value_modifier is not None:
            value = self.value_modifier.to_python(value)
            if value not in self.option_keys:
                return _NoValue
            if self.default_op and value == -1:
                return _NoValue
        return value

    def apply(self, query):
        if self.op == 'is':
            if len(self.value1) == 1:
                return query.filter(self.sa_col == self.value1[0])
            elif len(self.value1) > 1:
                return query.filter(self.sa_col.in_(self.value1))
            else:
                return query
        if self.op == '!is':
            if len(self.value1) == 1:
                return query.filter(self.sa_col != self.value1[0])
            elif len(self.value1) > 1:
                return query.filter(~self.sa_col.in_(self.value1))
            else:
                return query
        return FilterBase.apply(self, query)

class TextFilter(FilterBase):
    operators =  (ops.eq, ops.not_eq, ops.contains, ops.not_contains,
                    ops.empty, ops.not_empty)

    def apply(self, query):
        if self.op == 'contains':
            return query.filter(self.sa_col.like(u'%{0}%'.format(self.value1)))
        if self.op == '!contains':
            return query.filter(~self.sa_col.like(u'%{0}%'.format(self.value1)))
        if self.op == 'empty':
            return query.filter(or_(
                self.sa_col == None,
                self.sa_col == u'',
            ))
        if self.op == '!empty':
            return query.filter(and_(
                self.sa_col != None,
                self.sa_col != u'',
            ))
        return FilterBase.apply(self, query)

class NumberFilterBase(FilterBase):
    operators =  (ops.eq, ops.not_eq, ops.less_than_equal,
                    ops.greater_than_equal, ops.empty, ops.not_empty)

    def process(self, value, is_value2):
        if self.op in ('eq','!eq','lte','gte') and not is_value2:
            return self.validator(not_empty=True).to_python(value)
        return self.validator.to_python(value)

class IntFilter(NumberFilterBase):
    validator = feval.Int

class NumberFilter(NumberFilterBase):
    """
        Same as int filter, but will handle real numbers and type
        everything as a decimal.Decimal object
    """
    # our process() doesn't use a validator to return, but parent class does
    validator = feval.Number

    def process(self, value, is_value2):
        # call the validator to ensure the value is in the right format, but
        # don't use its value b/c it converts to float
        NumberFilterBase.process(self, value, is_value2)
        if value is None or (isinstance(value,basestring) and not len(value)):
            return None
        return D(value)

class DateFilter(FilterBase):
    operators =  (ops.eq, ops.not_eq, ops.less_than_equal,
                    ops.greater_than_equal, ops.between, ops.not_between,
                    ops.days_ago, ops.less_than_days_ago, ops.more_than_days_ago,
                    ops.today, ops.this_week, ops.in_days, ops.in_less_than_days,
                    ops.in_more_than_days, ops.empty, ops.not_empty)
    days_operators = 'da', 'ltda', 'mtda', 'iltd', 'imtd', 'ind'
    input_types = 'input', 'input2'

    def __init__(self, sa_col, _now=None, default_op=None):
        FilterBase.__init__(self, sa_col, default_op=default_op)
        # attributes from static instance
        self._now = _now

        # attributes that will start fresh for each instance
        self._was_time_given1 = False
        self._was_time_given2 = False

    def _get_now(self):
        return self._now or dt.datetime.now()

    def _get_today(self):
        # this filter is date-only, so our "now" is a date without time
        return ensure_date(self._get_now())

    def apply(self, query):
        today = self._get_today()

        if self.op in ('between', '!between'):
            if self.value1 <= self.value2:
                left_side = self.value1
                right_side = self.value2
            else:
                left_side = self.value2
                right_side = self.value1
            if self.op == 'between':
                return query.filter(self.sa_col.between(left_side, right_side))
            else:
                return query.filter(~self.sa_col.between(left_side, right_side))

        if self.op in ('da', 'ltda', 'mtda'):
            target_date = today - dt.timedelta(days=self.value1)
            if self.op == 'ltda':
                return query.filter(and_(
                    self.sa_col > target_date,
                    self.sa_col < today,
                ))
            if self.op == 'mtda':
                return query.filter(self.sa_col < target_date)
            # op == 'da'
            return query.filter(self.sa_col == target_date)

        if self.op in ('ind', 'iltd', 'imtd'):
            target_date = today + dt.timedelta(days=self.value1)
            if self.op == 'iltd':
                return query.filter(and_(
                    self.sa_col >= today,
                    self.sa_col < target_date
                ))
            if self.op == 'imtd':
                return query.filter(self.sa_col > target_date)
            # op == 'ind'
            return query.filter(self.sa_col == target_date)

        if self.op == 'today':
            return query.filter(self.sa_col == today)

        if self.op == 'thisweek':
            sunday = today - relativedelta(weekday=SU(-1))
            saturday = today + relativedelta(weekday=calendar.SATURDAY)
            return query.filter(self.sa_col.between(sunday, saturday))

        return FilterBase.apply(self, query)

    def process(self, value, is_value2):
        if value is None:
            return None

        if self.op in self.days_operators:
            return feval.Int(not_empty=True).to_python(value)

        try:
            return ensure_date(parse(value))
        except ValueError:
            raise formencode.Invalid('invalid date', value, self)
        except TypeError, e:
            # can probably be removed if this ever gets fixed:
            # https://bugs.launchpad.net/dateutil/+bug/1257985
            if "'NoneType' object is not iterable" not in str(e):
                raise
            raise formencode.Invalid('invalid date (parsing exception)', value, self)


class DateTimeFilter(DateFilter):

    def process(self, value, is_value2):
        if value is None:
            return None

        if self.op in self.days_operators:
            return feval.Int(not_empty=True).to_python(value)

        try:
            dt_value = parse(value)
        except ValueError:
            raise formencode.Invalid('invalid date', value, self)
        except TypeError, e:
            # can probably be removed if this ever gets fixed:
            # https://bugs.launchpad.net/dateutil/+bug/1257985
            if "'NoneType' object is not iterable" not in str(e):
                raise
            raise formencode.Invalid('invalid date (parsing exception)', value, self)


        if is_value2:
            self._has_date_only2 = self._has_date_only(dt_value, value)
        else:
            self._has_date_only1 = self._has_date_only(dt_value, value)

        return dt_value

    def _has_date_only(self, dt_value, value):
        return bool(dt_value.hour == 0 and
               dt_value.minute == 0 and
               dt_value.second == 0 and
               '00:00' not in value)

    def apply(self, query):
        today = self._get_today()

        if self.op in ('da', 'ltda', 'mtda'):
            target_date = today - dt.timedelta(days=self.value1)
            if self.op == 'da':
                left_side = ensure_datetime(target_date)
                right_side = ensure_datetime(target_date, time_part=dt.time(23,59,59,999999))
                return query.filter(self.sa_col.between(left_side, right_side))
            if self.op == 'ltda':
                return query.filter(and_(
                    self.sa_col > ensure_datetime(target_date, time_part=dt.time(23,59,59,999999)),
                    self.sa_col < ensure_datetime(today),
                ))
            # else self.op == 'mtda'
            return query.filter(self.sa_col < ensure_datetime(target_date))

        if self.op in ('ind', 'iltd', 'imtd'):
            target_date = today + dt.timedelta(days=self.value1)
            now = self._get_now()
            if self.op == 'iltd':
                return query.filter(and_(
                    self.sa_col >= now,
                    self.sa_col < ensure_datetime(target_date),
                ))
            if self.op == 'imtd':
                return query.filter(self.sa_col > ensure_datetime(target_date, time_part=dt.time(23,59,59,999999)))
            # else self.op == 'ind'
            left_side = ensure_datetime(target_date)
            right_side = ensure_datetime(target_date, time_part=dt.time(23,59,59,999999))
            return query.filter(self.sa_col.between(left_side, right_side))

        if self.op == 'today':
            left_side = ensure_datetime(today)
            right_side = ensure_datetime(today, time_part=dt.time(23,59,59,999999))
            return query.filter(self.sa_col.between(left_side, right_side))

        if self.op == 'thisweek':
            sunday = today - relativedelta(weekday=SU(-1))
            saturday = today + relativedelta(weekday=calendar.SATURDAY)

            left_side = ensure_datetime(sunday)
            right_side = ensure_datetime(saturday, time_part=dt.time(23,59,59,999999))
            return query.filter(self.sa_col.between(left_side, right_side))

        # if this is an equal operation, but the date given did not have a time
        # portion, make the filter cover the whole day
        if self.op in ('eq', '!eq') and self._has_date_only1:
            left_side = ensure_datetime(self.value1.date())
            right_side = ensure_datetime(self.value1.date(), time_part=dt.time(23,59,59,999999))
            between_clause = self.sa_col.between(left_side, right_side)
            if self.op == 'eq':
                return query.filter(between_clause)
            else:
                return query.filter(~between_clause)

        if self.op == 'lte' and self._has_date_only1:
            value1 = ensure_datetime(self.value1.date(), time_part=dt.time(23,59,59,999999))
            return query.filter(self.sa_col <= value1)

        # sometimes we need to tweak the user given value if they have not
        # specified a time
        if self.op in ('between', '!between'):
            if self._has_date_only2:
                right_side = ensure_datetime(self.value2.date(), time_part=dt.time(23,59,59,999999))
            else:
                right_side = self.value2
            between_clause = self.sa_col.between(self.value1, right_side)
            if self.op == 'between':
                return query.filter(between_clause)
            else:
                return query.filter(~between_clause)


        return DateFilter.apply(self, query)
