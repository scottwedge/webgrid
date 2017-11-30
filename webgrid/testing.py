"""
A collection of utilities for testing webgrid functionality in client applications
"""

import xlrd


def assert_list_equal(list1, list2):
    """
    A list-specific equality assertion.

    This method is based on the Python `unittest.TestCase.assertListEqual` method.

    :param list1:
    :param list2:
    :return:
    """

    # resolve generators
    list1, list2 = map(list, (list1, list2))

    assert len(list1) == len(list2), \
        'Lists are different lengths: {} != {}'.format(
            len(list1),
            len(list2)
    )

    if list1 == list2:
        # the lists are the same, we're done
        return

    # the lists are different in at least one element; find it
    # and report it
    for index, (val1, val2) in enumerate(zip(list1, list2)):
        assert val1 == val2, (
            'First differing element at index {}: {} != {}'.format(
                index,
                repr(val1),
                repr(val2)
            )
        )


def assert_rendered_xls_matches(rendered_xls, xls_headers, xls_rows):
    """
    Verifies that `rendered_xls` has a set of headers and values that match
    the given parameters.

    NOTE: This method does not perform in-depth analysis of complex workbooks!
          Multiple worksheets or complex (multi-row) headers *are not verified!*

    :param rendered_xls:
    :param xls_headers:
    :param xls_rows:
    :return:
    :rtype: bool
    """
    assert rendered_xls
    workbook = xlrd.open_workbook(file_contents=rendered_xls)

    assert workbook.nsheets >= 1
    sheet = workbook.sheet_by_index(0)

    # # verify the shape of the sheet

    # ## shape of rows (1 row for the headers, 1 for each row of data)
    nrows = len(xls_rows)
    if xls_headers:
        nrows += 1
    assert nrows == sheet.nrows

    # ## shape of columns
    ncols = max(
        len(xls_headers) if xls_headers else 0,
        max(len(values) for values in xls_rows) if xls_rows else 0
    )
    assert ncols == sheet.ncols

    if xls_headers:
        assert_list_equal(
            (cell.value for cell in sheet.row(0)),
            xls_headers
        )

    if xls_rows:
        row_iter = sheet.get_rows()

        # skip header row
        if xls_headers:
            next(row_iter)

        for row, expected_row in zip(row_iter, xls_rows):
            assert_list_equal(
                (cell.value for cell in row),
                expected_row
            )
