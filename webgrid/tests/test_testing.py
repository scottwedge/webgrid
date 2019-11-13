import datetime as dt
from io import BytesIO
from nose.plugins.skip import SkipTest

import xlwt
from nose.tools import assert_raises

from webgrid import testing
from webgrid_ta.grids import TemporalGrid


class TestAssertListEqual:
    """Verify the `assert_list_equal` method performs as expected"""

    def test_simple_equivalents(self):
        testing.assert_list_equal([], [])
        testing.assert_list_equal([1, 2, 3], [1, 2, 3])
        testing.assert_list_equal((1, 2, 3), [1, 2, 3])
        testing.assert_list_equal('123', '123')

    def test_different_lengths(self):
        with assert_raises(AssertionError):
            testing.assert_list_equal([], [1])

        with assert_raises(AssertionError):
            testing.assert_list_equal([1], [])

    def test_different_elements(self):
        with assert_raises(AssertionError):
            testing.assert_list_equal([1, 2, 3], [1, 2, 4])

    def test_order_is_significant(self):
        with assert_raises(AssertionError):
            testing.assert_list_equal([1, 2, 3], [2, 3, 1])

    def test_generators(self):
        testing.assert_list_equal((x for x in range(3)), (x for x in range(3)))
        testing.assert_list_equal((x for x in range(3)), [0, 1, 2])
        testing.assert_list_equal([0, 1, 2], (x for x in range(3)))


class TestAssertRenderedXlsMatches:
    def setup(self):
        self.workbook = xlwt.Workbook()
        self.sheet = self.workbook.add_sheet('sheet1')
        self.stream = BytesIO()

        self.headers_written = False

    def set_headers(self, headers):
        for index, header in enumerate(headers):
            self.sheet.write(0, index, header)

        self.headers_written = True

    def set_values(self, values):
        row_offset = 0

        if self.headers_written:
            row_offset = 1

        for row_index, row in enumerate(values, start=row_offset):
            for col_index, value in enumerate(row):
                self.sheet.write(row_index, col_index, value)

    def assert_matches(self, xls_headers, xls_rows):
        self.workbook.save(self.stream)
        testing.assert_rendered_xls_matches(self.stream.getvalue(), xls_headers, xls_rows)

    def test_empty_xls(self):
        with assert_raises(AssertionError):
            testing.assert_rendered_xls_matches(b'', None, None)

        with assert_raises(AssertionError):
            testing.assert_rendered_xls_matches(None, None, None)

        with assert_raises(AssertionError):
            testing.assert_rendered_xls_matches(None, [], [])

    def test_blank_workbook(self):
        self.assert_matches([], [])

    def test_single_header(self):
        self.set_headers(['Foo'])
        self.assert_matches(['Foo'], [])

    def test_multiple_headers(self):
        self.set_headers(['Foo', 'Bar'])
        self.assert_matches(['Foo', 'Bar'], [])

    def test_single_row(self):
        self.set_values([[1, 2, 3]])
        self.assert_matches([], [[1, 2, 3]])

    def test_multiple_rows(self):
        self.set_values([
            [1, 2, 3],
            [2, 3, 4]
        ])

        self.assert_matches([], [
            [1, 2, 3],
            [2, 3, 4]
        ])

    def test_headers_and_rows(self):
        self.set_headers(['Foo', 'Bar'])
        self.set_values([
            [1, 2],
            [2, 3],
            [3, 4]
        ])

        self.assert_matches(
            ['Foo', 'Bar'],
            [
                [1, 2],
                [2, 3],
                [3, 4]
            ]
        )

    def test_value_types(self):
        self.set_values([
            [1, 1.23, 'hello', None, True, False]
        ])

        self.assert_matches([], [
            [1, 1.23, 'hello', '', True, False]
        ])

    def test_none_is_mangled(self):
        self.set_values([
            [None, 1, 1.23, 'hello', None]
        ])

        # the left `None` becomes an empty string
        # the right `None` gets dropped
        self.assert_matches([], [
            ['', 1, 1.23, 'hello']
        ])


# postgres-only test
@SkipTest
class TestPGCompilerMixin(testing.PGCompilerMixin, testing.GridBase):
    grid_cls = TemporalGrid

    @property
    def filters(self):
        return (
            ('createdts', 'eq', dt.datetime(2018, 1, 1, 5, 30),
             "WHERE persons.createdts = '2018-01-01 05:30:00.000000'"),
            ('due_date', 'eq', dt.date(2018, 1, 1), "WHERE persons.due_date = '2018-01-01'"),
            ('start_time', 'eq', dt.time(1, 30).strftime('%I:%M %p'),
             "WHERE persons.start_time = CAST('01:30' AS TIME WITHOUT TIME ZONE)"),
        )


# sql server-only test
@SkipTest
class TestMSSQLCompilerMixin(testing.MSSQLCompilerMixin, testing.GridBase):
    grid_cls = TemporalGrid

    @property
    def filters(self):
        return (
            ('createdts', 'eq', dt.datetime(2018, 1, 1, 5, 30),
             "WHERE persons.createdts = '2018-01-01 05:30:00.000000'"),
            ('due_date', 'eq', '2018-01-01', "WHERE persons.due_date = '2018-01-01'"),
            ('start_time', 'eq', dt.time(1, 30).strftime('%I:%M %p'),
             "WHERE persons.start_time = CAST('01:30' AS TIME)"),
        )
