from __future__ import absolute_import
import calendar
import datetime as dt
from decimal import Decimal as D
import inspect

from blazeutils import tolist
from blazeutils.dates import ensure_date, ensure_datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta, SU
import formencode
import formencode.validators as feval
from sqlalchemy.sql import or_, and_
import sqlalchemy as sa
import six


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
    this_month = Operator('thismonth', 'this month', None)
    last_month = Operator('lastmonth', 'last month', None)
    select_month = Operator('selmonth', 'select month', 'select+input')
    this_year = Operator('thisyear', 'this year', None)


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

    def __init__(self, sa_col, default_op=None, default_value1=None, default_value2=None,
                 dialect=None):
        # attributes from static instance
        self.sa_col = sa_col
        self.default_op = default_op
        self.default_value1 = default_value1
        self.default_value2 = default_value2
        self.dialect = dialect

        # attributes that will start fresh for each instance
        self.op = None
        self.value1 = None
        self.value2 = None
        self.value1_set_with = None
        self.value2_set_with = None
        self._op_keys = None
        self.error = False

        # find the outermost call to a subclass's init method so we can store the exact arguments
        # used to construct it
        outermost = None
        frame = inspect.currentframe()
        # Can't use inspect.stack() here because when called from within a Jinja template,
        # inspect.getframeinfo raises an exception
        while frame:
            if frame.f_code.co_name != '__init__' or \
                    not isinstance(frame.f_locals.get('self'), FilterBase):
                break
            outermost = inspect.getargvalues(frame)
            frame = frame.f_back

        self._vargs = [outermost.locals[a] for a in outermost.args[1:]] + \
            list(outermost.locals[outermost.varargs] if outermost.varargs else [])

        self._kwargs = outermost.locals[outermost.keywords] if outermost.keywords else {}

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

    def _default_value(self, value):
        if callable(value):
            return value()
        return value

    def set(self, op, value1, value2=None):
        if not op:
            self.op = self.default_op
            self.using_default_op = (self.default_op is not None)
            if self.op is None:
                return

        if not op and self.using_default_op:
            value1 = self._default_value(self.default_value1)
            value2 = self._default_value(self.default_value2)

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
        if self.op == self.default_op and self.value1 is None:
            return query
        if self.op == 'eq':
            return query.filter(self.sa_col == self.value1)
        if self.op == '!eq':
            return query.filter(self.sa_col != self.value1)
        if self.op == 'empty':
            return query.filter(self.sa_col.is_(None))
        if self.op == '!empty':
            return query.filter(self.sa_col.isnot(None))
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

    def new_instance(self, **kwargs):
        """
        Note: Ensure any overrides of this method accept and pass through kwargs to preserve
        compatibility in future
        """
        cls = self.__class__
        new_filter = cls(*self._vargs, **self._kwargs)
        new_filter.dialect = kwargs.get('dialect')
        return new_filter


class _NoValue(object):
    pass


class OptionsFilterBase(FilterBase):
    operators = ops.is_, ops.not_is, ops.empty, ops.not_empty
    input_types = 'select'
    receives_list = True
    options_from = ()

    def __init__(self, sa_col, value_modifier='auto', default_op=None, default_value1=None,
                 default_value2=None):
        FilterBase.__init__(self, sa_col, default_op=default_op, default_value1=default_value1,
                            default_value2=default_value2)
        # attributes from static instance
        self.value_modifier = value_modifier

        # attributes that will start fresh for each instance
        self._options_seq = None
        self._options_keys = None

    def new_instance(self, **kwargs):
        filter = FilterBase.new_instance(self, **kwargs)
        filter.setup_validator()
        return filter

    @property
    def options_seq(self):
        if self._options_seq is None:
            try:
                self._options_seq = self.options_from()
            except TypeError as e:
                if 'is not callable' not in str(e):
                    raise
                self._options_seq = self.options_from
            if self.default_op:
                self._options_seq = [(-1, '-- All --')] + list(self._options_seq)
        return self._options_seq

    @property
    def option_keys(self):
        if self._options_keys is None:
            self._options_keys = [k for k, v in self.options_seq]
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
            if isinstance(first_key, six.string_types) or self.value_modifier is None:
                self.value_modifier = feval.UnicodeString
            # this didn't work right, so commenting out for now
            # elif isinstance(first_key, bool):
            #    self.value_modifier = formencode.compound.Any(feval.Bool, feval.StringBoolean)
            elif isinstance(first_key, int):
                self.value_modifier = feval.Int
            elif isinstance(first_key, float):
                self.value_modifier = feval.Number
            elif isinstance(first_key, D):
                self.value_modifier = feval.Wrapper(to_python=D)
            else:
                raise TypeError(
                    "can't use value_modifier='auto' when option keys are {0}".format(
                        type(first_key)
                    )
                )
        else:
            # if its not the string 'auto' and its not a formencode validator, assume
            # its a callable and wrap with a formencode validator
            if not hasattr(self.value_modifier, 'to_python'):
                if not hasattr(self.value_modifier, '__call__'):
                    raise TypeError(
                        'value_modifier must be the string "auto", have a "to_python" attribute, '
                        'or be a callable'
                    )
                self.value_modifier = feval.Wrapper(to_python=self.value_modifier)

    def set(self, op, values, value2=None):
        if not op and not self.default_op:
            return
        self.op = op or self.default_op
        self.using_default_op = (self.default_op is not None)

        if self.using_default_op and op is None and self.default_value1 is not None:
            values = tolist(self._default_value(self.default_value1))

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


class OptionsIntFilterBase(OptionsFilterBase):
    def __init__(self, sa_col, value_modifier=feval.Int, default_op=None, default_value1=None,
                 default_value2=None):
        OptionsFilterBase.__init__(self, sa_col, value_modifier, default_op, default_value1,
                                   default_value2)


class TextFilter(FilterBase):
    operators = (ops.eq, ops.not_eq, ops.contains, ops.not_contains, ops.empty, ops.not_empty)

    @property
    def comparisons(self):
        if self.dialect and self.dialect.name in ('postgresql', 'sqlite'):
            return {
                'eq': lambda col, value: sa.func.upper(col) == sa.func.upper(value),
                '!eq': lambda col, value: sa.func.upper(col) != sa.func.upper(value),
                'contains': lambda col, value: col.ilike(u'%{}%'.format(value)),
                '!contains': lambda col, value: ~col.ilike(u'%{}%'.format(value))
            }
        return {
            'eq': lambda col, value: col == value,
            '!eq': lambda col, value: col != value,
            'contains': lambda col, value: col.like(u'%{}%'.format(value)),
            '!contains': lambda col, value: ~col.like(u'%{}%'.format(value))
        }

    def apply(self, query):
        if self.op == self.default_op and not self.value1:
            return query
        if self.op == 'empty':
            return query.filter(or_(
                self.sa_col.is_(None),
                self.sa_col == u'',
            ))
        if self.op == '!empty':
            return query.filter(and_(
                self.sa_col.isnot(None),
                self.sa_col != u'',
            ))

        if self.op in self.comparisons:
            return query.filter(self.comparisons[self.op](self.sa_col, self.value1))
        return FilterBase.apply(self, query)


class NumberFilterBase(FilterBase):
    operators = (ops.eq, ops.not_eq, ops.less_than_equal, ops.greater_than_equal, ops.empty,
                 ops.not_empty)

    def process(self, value, is_value2):
        if self.op == self.default_op and not value:
            return None
        if self.op in ('eq', '!eq', 'lte', 'gte') and not is_value2:
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
        if value is None or (isinstance(value, six.string_types) and not len(value)):
            return None
        return D(value)


class _DateMixin(object):
    options_from = [
        (1, '01-Jan'), (2, '02-Feb'), (3, '03-Mar'), (4, '04-Apr'),
        (5, '05-May'), (6, '06-Jun'), (7, '07-Jul'), (8, '08-Aug'),
        (9, '09-Sep'), (10, '10-Oct'), (11, '11-Nov'), (12, '12-Dec'),
    ]

    @property
    def options_seq(self):
        _options_seq = self.options_from
        if self.default_op:
            _options_seq = [(-1, '-- All --')] + _options_seq
        return _options_seq

    def format_display_vals(self):
        if isinstance(self.value1, dt.date) and self.op in (
            ops.eq.key,
            ops.not_eq.key,
            ops.less_than_equal.key,
            ops.greater_than_equal.key,
            ops.between.key,
            ops.not_between.key
        ):
            self.value1_set_with = self.value1.strftime('%m/%d/%Y')
        if isinstance(self.value2, dt.date) and self.op in (
            ops.between.key,
            ops.not_between.key
        ):
            self.value2_set_with = self.value2.strftime('%m/%d/%Y')

    """
        String description of the filter operation and values
        - Useful for Excel reports
    """
    @property
    def description(self):
        today = self._get_today()
        last_day = first_day = None
        prefix = ''

        if self.error:
            return 'invalid'

        # these filters can be set as default ops without input values, so don't ignore them
        if self.op == 'thismonth':
            last_day = today + relativedelta(day=1, months=+1, days=-1)
            first_day = today + relativedelta(day=1)
        elif self.op == 'lastmonth':
            last_day = today + relativedelta(day=1, days=-1)
            first_day = today + relativedelta(day=1, months=-1)
        elif self.op == 'thisyear':
            last_day = dt.date(today.year, 12, 31)
            first_day = dt.date(today.year, 1, 1)
        elif self.op == 'thisweek':
            first_day = today - relativedelta(weekday=SU(-1))
            last_day = today + relativedelta(weekday=calendar.SATURDAY)
        elif self.op == 'today':
            first_day = today

        if not first_day and (
            not self.op or (
                self.default_op == self.op and (
                    self.value2 is None and self.value1 is None
                )
            )
        ):
            return 'all'

        # ops with both dates populated
        if self.op == 'selmonth':
            if not (
                isinstance(self.value1, int) and isinstance(self.value2, int)
            ):
                return 'All'
            if self.value1 < 1 or self.value1 > 12:
                return self.value2
            return dt.date(self.value2, self.value1, 1).strftime('%b %Y')
        elif self.op in ('between', '!between'):
            if self.value1 <= self.value2:
                first_day = self.value1
                last_day = self.value2
            else:
                first_day = self.value2
                last_day = self.value1
            if self.op == '!between':
                prefix = 'excluding '
        elif self.op == 'ltda':
            first_day = today - dt.timedelta(days=self.value1)
            last_day = today
        elif self.op == 'iltd':
            last_day = today + dt.timedelta(days=self.value1)
            first_day = today

        if last_day and first_day:
            return '{0}{1} - {2}'.format(
                prefix,
                first_day.strftime('%m/%d/%Y'),
                last_day.strftime('%m/%d/%Y')
            )

        # ops with single date populated
        if self.op in ('da', 'mtda'):
            first_day = today - dt.timedelta(days=self.value1)
            if self.op == 'mtda':
                prefix = 'before '
        elif self.op in ('ind', 'imtd'):
            first_day = today + dt.timedelta(days=self.value1)
            if self.op == 'imtd':
                prefix = 'after '
        elif self.op == 'empty':
            return 'date not specified'
        elif self.op == '!empty':
            return 'any date'
        elif self.op in ('eq', '!eq', 'lte', 'gte'):
            first_day = self.value1
            if self.op == '!eq':
                prefix = 'excluding '
            elif self.op == 'lte':
                prefix = 'up to '
            elif self.op == 'gte':
                prefix = 'beginning '
        return '{0}{1}'.format(
            prefix,
            first_day.strftime('%m/%d/%Y')
        )


class DateFilter(FilterBase, _DateMixin):
    operators = (
        ops.eq, ops.not_eq, ops.less_than_equal,
        ops.greater_than_equal, ops.between, ops.not_between,
        ops.days_ago, ops.less_than_days_ago, ops.more_than_days_ago,
        ops.today, ops.this_week, ops.in_days, ops.in_less_than_days,
        ops.in_more_than_days, ops.empty, ops.not_empty, ops.this_month,
        ops.last_month, ops.select_month, ops.this_year
    )
    days_operators = 'da', 'ltda', 'mtda', 'iltd', 'imtd', 'ind'
    no_value_operators = (
        'empty', '!empty', 'today', 'thisweek', 'thismonth', 'lastmonth', 'thisyear'
    )
    input_types = 'input', 'select', 'input2'

    def __init__(self, sa_col, _now=None, default_op=None, default_value1=None,
                 default_value2=None):
        self.first_day = None
        self.last_day = None
        FilterBase.__init__(self, sa_col, default_op=default_op, default_value1=default_value1,
                            default_value2=default_value2)
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

    def set(self, op, value1, value2=None):
        super(DateFilter, self).set(op, value1, value2)
        self.format_display_vals()

        # store first/last day for customized usage
        today = self._get_today()
        first_day = last_day = None
        if self.op == 'thismonth':
            last_day = today + relativedelta(day=1, months=+1, days=-1)
            first_day = today + relativedelta(day=1)
        elif self.op == 'lastmonth':
            last_day = today + relativedelta(day=1, days=-1)
            first_day = today + relativedelta(day=1, months=-1)
        elif self.op == 'selmonth':
            if not self.value2:
                return
            month = self.value1 if self.value1 > 0 else 1
            first_day = dt.date(self.value2, month, 1)
            last_day = first_day + relativedelta(day=1, months=+1, days=-1)
            if self.value1 == -1:
                last_day = dt.date(self.value2, 12, 31)
        elif self.op == 'thisyear':
            last_day = dt.date(today.year, 12, 31)
            first_day = dt.date(today.year, 1, 1)
        elif self.op in ('between', '!between'):
            if self.value1 <= self.value2:
                first_day = self.value1
                last_day = self.value2
            else:
                first_day = self.value2
                last_day = self.value1
        elif self.op in ('da', 'ltda', 'mtda'):
            target_date = today - dt.timedelta(days=self.value1)
            if self.op == 'ltda':
                first_day = target_date
                last_day = today
            elif self.op == 'mtda':
                first_day = None
                last_day = target_date
            elif self.op == 'da':
                first_day = last_day = target_date
        elif self.op == 'today':
            first_day = last_day = today
        elif self.op == 'thisweek':
            sunday = today - relativedelta(weekday=SU(-1))
            saturday = today + relativedelta(weekday=calendar.SATURDAY)
            first_day = sunday
            last_day = saturday
        elif self.op == 'eq':
            first_day = last_day = self.value1

        self.first_day = first_day
        self.last_day = last_day

    def apply(self, query):
        today = self._get_today()

        if self.op == 'today':
            return query.filter(self.sa_col == today)

        if self.op == 'thisweek':
            sunday = today - relativedelta(weekday=SU(-1))
            saturday = today + relativedelta(weekday=calendar.SATURDAY)
            return query.filter(self.sa_col.between(sunday, saturday))

        if self.op == 'selmonth' and not (self.value1 and self.value2):
            return query

        if self.op in ('thismonth', 'lastmonth', 'selmonth', 'thisyear',):
            return query.filter(self.sa_col.between(
                self.first_day,
                self.last_day
            ))

        # filters above are handled specifically before this check because they do not require any
        #   input values (or selmonth, which is grouped and handled specially). Filters below this
        #   need at least one value to proceed, and if a default value is displayed but not
        #   populated, we need to ignore it
        if self.op == self.default_op and self.value1 is None:
            return query

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

        return FilterBase.apply(self, query)

    def process(self, value, is_value2):
        if value is None or self.op in self.no_value_operators:
            return None

        if self.op == self.default_op and not value:
            return None

        if self.op == 'selmonth':
            if is_value2:
                return feval.Int(not_empty=False, min=1900, max=9999).to_python(value)
            return feval.Int(not_empty=False).to_python(value)

        if self.op in self.days_operators:
            if is_value2:
                return None
            filter_value = feval.Int(not_empty=True).to_python(value)

            if self.op in ('da', 'ltda', 'mtda'):
                try:
                    self._get_today() - dt.timedelta(days=filter_value)
                except OverflowError:
                    raise formencode.Invalid('date filter given is out of range', value, self)

            if self.op in ('ind', 'iltd', 'imtd'):
                try:
                    self._get_today() + dt.timedelta(days=filter_value)
                except OverflowError:
                    raise formencode.Invalid('date filter given is out of range', value, self)

            return filter_value

        try:
            d = ensure_date(parse(value))

            if isinstance(d, (dt.date, dt.datetime)) and d.year < 1900:
                return feval.Int(min=1900).to_python(d.year)

            return d
        except ValueError:
            # allow open ranges when blanks are submitted as a second value
            if is_value2 and not value:
                return dt.date.today()

            raise formencode.Invalid('invalid date', value, self)


class DateTimeFilter(DateFilter):
    def __init__(self, sa_col, _now=None, default_op=None, default_value1=None,
                 default_value2=None):
        self._has_date_only1 = self._has_date_only2 = False
        super(DateTimeFilter, self).__init__(sa_col, _now=_now, default_op=default_op,
                                             default_value1=default_value1,
                                             default_value2=default_value2)

    def format_display_vals(self):
        ops_single_val = (
            ops.eq.key,
            ops.not_eq.key,
            ops.less_than_equal.key,
            ops.greater_than_equal.key,
        )
        ops_double_val = (
            ops.between.key,
            ops.not_between.key
        )
        if isinstance(self.value1, dt.datetime) and self.op in ops_single_val + ops_double_val:
            self.value1_set_with = self.value1.strftime('%m/%d/%Y %I:%M %p')
            if self.op in ops_single_val and self._has_date_only1:
                self.value1_set_with = self.value1.strftime('%m/%d/%Y')
        if isinstance(self.value2, dt.datetime) and self.op in ops_double_val:
            self.value2_set_with = self.value2.strftime('%m/%d/%Y %I:%M %p')
            if self._has_date_only2:
                self.value2_set_with = self.value2.strftime('%m/%d/%Y 11:59 PM')

    def process(self, value, is_value2):
        if value is None:
            return None

        if self.op == self.default_op and not value:
            return None

        if self.op == 'selmonth':
            if is_value2:
                return feval.Int(not_empty=False, min=1900, max=9999).to_python(value)
            return feval.Int(not_empty=False).to_python(value)

        if self.op in self.days_operators:
            if is_value2:
                return None

            filter_value = feval.Int(not_empty=True).to_python(value)

            if self.op in ('da', 'ltda', 'mtda'):
                try:
                    self._get_today() - dt.timedelta(days=filter_value)
                except OverflowError:
                    raise formencode.Invalid('date filter given is out of range', value, self)

            if self.op in ('ind', 'iltd', 'imtd'):
                try:
                    self._get_today() + dt.timedelta(days=filter_value)
                except OverflowError:
                    raise formencode.Invalid('date filter given is out of range', value, self)

            return filter_value
        elif value == '' and self.op in self.no_value_operators:
            return None

        try:
            dt_value = parse(value)
        except ValueError:
            raise formencode.Invalid('invalid date', value, self)

        if is_value2:
            self._has_date_only2 = self._has_date_only(dt_value, value)
        else:
            self._has_date_only1 = self._has_date_only(dt_value, value)

        return dt_value

    def _has_date_only(self, dt_value, value):
        return bool(
            dt_value.hour == 0 and
            dt_value.minute == 0 and
            dt_value.second == 0 and
            '00:00' not in value
        )

    def apply(self, query):
        today = self._get_today()

        if self.op == 'today':
            left_side = ensure_datetime(today)
            right_side = ensure_datetime(today, time_part=dt.time(23, 59, 59, 999999))
            return query.filter(self.sa_col.between(left_side, right_side))

        if self.op == 'thisweek':
            sunday = today - relativedelta(weekday=SU(-1))
            saturday = today + relativedelta(weekday=calendar.SATURDAY)

            left_side = ensure_datetime(sunday)
            right_side = ensure_datetime(saturday, time_part=dt.time(23, 59, 59, 999999))
            return query.filter(self.sa_col.between(left_side, right_side))

        if self.op == 'thismonth':
            last_day = today + relativedelta(day=1, months=+1, microseconds=-1)
            first_day = ensure_datetime(today + relativedelta(day=1))
            return query.filter(self.sa_col.between(first_day, last_day))

        if self.op == 'lastmonth':
            last_day = today + relativedelta(day=1, microseconds=-1)
            first_day = ensure_datetime(today + relativedelta(day=1, months=-1))
            return query.filter(self.sa_col.between(first_day, last_day))

        if self.op == 'thisyear':
            last_day = today + relativedelta(day=31, month=12, days=+1, microseconds=-1)
            first_day = ensure_datetime(today + relativedelta(day=1, month=1))
            return query.filter(self.sa_col.between(first_day, last_day))

        if self.op == 'selmonth' and not self.value2:
            return query

        if self.op == 'selmonth':
            first_day = ensure_datetime(self.first_day)
            last_day = self.last_day + relativedelta(days=1, microseconds=-1)
            return query.filter(self.sa_col.between(first_day, last_day))

        # filters above are handled specifically before this check because they do not require any
        #   input values (or selmonth, which is grouped and handled specially). Filters below this
        #   need at least one value to proceed, and if a default value is displayed but not
        #   populated, we need to ignore it
        if self.op == self.default_op and self.value1 is None:
            return query

        if self.op in ('da', 'ltda', 'mtda'):
            target_date = today - dt.timedelta(days=self.value1)
            if self.op == 'da':
                left_side = ensure_datetime(target_date)
                right_side = ensure_datetime(target_date, time_part=dt.time(23, 59, 59, 999999))
                return query.filter(self.sa_col.between(left_side, right_side))
            if self.op == 'ltda':
                return query.filter(and_(
                    self.sa_col > ensure_datetime(target_date,
                                                  time_part=dt.time(23, 59, 59, 999999)),
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
                return query.filter(
                    self.sa_col > ensure_datetime(target_date,
                                                  time_part=dt.time(23, 59, 59, 999999))
                )
            # else self.op == 'ind'
            left_side = ensure_datetime(target_date)
            right_side = ensure_datetime(target_date, time_part=dt.time(23, 59, 59, 999999))
            return query.filter(self.sa_col.between(left_side, right_side))

        # if this is an equal operation, but the date given did not have a time
        # portion, make the filter cover the whole day
        if self.op in ('eq', '!eq') and self._has_date_only1:
            left_side = ensure_datetime(self.value1.date())
            right_side = ensure_datetime(self.value1.date(), time_part=dt.time(23, 59, 59, 999999))
            between_clause = self.sa_col.between(left_side, right_side)
            if self.op == 'eq':
                return query.filter(between_clause)
            else:
                return query.filter(~between_clause)

        if self.op == 'lte' and self._has_date_only1:
            value1 = ensure_datetime(self.value1.date(), time_part=dt.time(23, 59, 59, 999999))
            return query.filter(self.sa_col <= value1)

        # sometimes we need to tweak the user given value if they have not
        # specified a time
        if self.op in ('between', '!between'):
            if self._has_date_only2:
                right_side = ensure_datetime(self.value2.date(),
                                             time_part=dt.time(23, 59, 59, 999999))
            else:
                right_side = self.value2
            between_clause = self.sa_col.between(ensure_datetime(self.value1), right_side)
            if self.op == 'between':
                return query.filter(between_clause)
            else:
                return query.filter(~between_clause)

        return DateFilter.apply(self, query)


class TimeFilter(FilterBase):
    operators = (ops.eq, ops.not_eq, ops.less_than_equal, ops.greater_than_equal, ops.between,
                 ops.not_between, ops.empty, ops.not_empty)
    input_types = 'input', 'input2'

    time_format = '%I:%M %p'

    def apply(self, query):
        if self.op == self.default_op and self.value1 is None:
            return query

        if self.op in ('between', '!between'):
            left = min(self.value1, self.value2)
            right = max(self.value1, self.value2)
            cond = self.sa_col.between(sa.cast(left, sa.Time), sa.cast(right, sa.Time))
            if self.op == '!between':
                cond = ~cond
            return query.filter(cond)

        # Casting this because some SQLAlchemy dialects (MSSQL) convert the value to datetime
        # before binding.
        val = sa.cast(self.value1, sa.Time)

        if self.op == 'eq':
            query = query.filter(self.sa_col == val)
        elif self.op == '!eq':
            query = query.filter(self.sa_col != val)
        elif self.op == 'lte':
            query = query.filter(self.sa_col <= val)
        elif self.op == 'gte':
            query = query.filter(self.sa_col >= val)
        else:
            query = super(TimeFilter, self).apply(query)
        return query

    def process(self, value, is_value2):
        if value in (None, ''):
            return None

        if self.op == self.default_op and not value:
            return None

        try:
            return dt.datetime.strptime(value, self.time_format).time()
        except ValueError:
            raise formencode.Invalid('invalid time', value, self)


class YesNoFilter(FilterBase):
    operators = (
        Operator('a', 'all', None),
        Operator('y', 'yes', None),
        Operator('n', 'no', None),
    )

    def apply(self, query):
        if self.op == 'a':
            return query
        if self.op == 'y':
            return query.filter(self.sa_col == sa.true())
        if self.op == 'n':
            return query.filter(self.sa_col == sa.false())
        return FilterBase.apply(self, query)
