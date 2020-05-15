WebGrid
#######

.. image:: https://ci.appveyor.com/api/projects/status/6s1886gojqi9c8h6?svg=true
    :target: https://ci.appveyor.com/project/level12/webgrid

.. image:: https://circleci.com/gh/level12/webgrid.svg?style=shield
    :target: https://circleci.com/gh/level12/webgrid

.. image:: https://codecov.io/gh/level12/webgrid/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/level12/webgrid

Introduction
---------------

WebGrid is a datagrid library for Flask and other Python web frameworks designed to work with
SQLAlchemy ORM entities.

Based on the configured grid, it will output an HTML table with sorting, filtering, and paging.

It also will export the grid to Excel.

For now, if you are interested in using it, you will need to see the source code and tests therein
for example usage.

Features
--------

Filter/Search
=============

Webgrid columns may be assigned filters that will be available in the UI for the user to narrow
down grid records. Filters are self-contained query modifiers: they take the column/expression to
be filtered, and the query to filter, and apply their own logic based on the selected operator.

Example:

.. code::

    class MyGrid(Grid):
        Column('Name', Person.name, TextFilter)

Default operator and default filter value (or values, up to two) may be set in the constructor.
Default filters are enforced to show up on the UI at all times without the user selecting them, but
the user may reconfigure the options for that filter:

.. code::

    class MyGrid(Grid):
        Column('Name', Person.name, TextFilter(Person.name, default_op='contains', default_value1='Smith'))

Webgrid also uses filters to support a generic search. Use the `enable_search` boolean flag on the
grid to turn on a search box, which will poll all available filters for search expressions to OR
on a query:

.. code::

    class MyGrid(Grid):
        enable_search = True

        Column('Name', Person.name, TextFilter)

Custom filters need to subclass `FilterBase`. The `operators` attribute will define what options are
available in the UI. The `apply` method takes the grid query and returns a modified query having the
filter. To have the filter support generic search, it needs to override `get_search_expr` to return
a callable that takes the search value and returns a SQLAlchemy expression. Examples may be found
in `webgrid.filters`.

Render Specifiers
=================

The column is visible in renderers specified in `render_in`.
`render_in` may be:
- an iterable of strings
- a string
- a lambda which accepts the column instance and returns a string or iterable of strings
`render_in` is overridden if `visible` is `False`.

Visiblity
=========

The column is visible when `visible` is `True`.
`visible` may be:
- a boolean
- a lambda which accepts the column instance and returns a boolean

Column Groups
=============

Columns can be grouped under a common header by passing a  ``group`` (a ``ColumnGroup`` subclass
or an instance of ``ColumnGroup``) to ``Column`` constructors. See
``webgrid_ta.grids.StopwatchGrid`` for an example. View ``/groups`` endpoint to see column groups
in action.

Questions & Comments
---------------------

Please visit: http://groups.google.com/group/blazelibs

Running the Tests
-----------------

Make sure to include the ``--nologcapture`` flag to nosetests or else you will get
failures when testing the logging features.

Current Status
---------------

Currently beta quality.

Translations
------------

Helpful links
=============

 * https://www.gnu.org/software/gettext/manual/html_node/Mark-Keywords.html
 * https://www.gnu.org/software/gettext/manual/html_node/Preparing-Strings.html


Message management
==================

The ``setup.cfg`` file is configured to handle the standard message extraction commands. For ease of development
and ensuring that all marked strings have translations, a tox environment is defined for testing i18n. This will
run commands to update and compile the catalogs, and specify any strings which need to be added.

The desired workflow here is to run tox, update strings in the PO files as necessary, run tox again
(until it passes), and then commit the changes to the catalog files.

.. code::

    tox -e i18n


Upgrading
---------

Upgrading to v0.1.38
====================

The i18n support added in v0.1.38 introduces a slight change which could affect existing
installations, related to the handling of "table totals" labels.

In versions prior to v0.1.38, the word 'Totals' (ie, "Page Totals" or "Grand Totals") was added by the
`renderers.HTML.table_totals` method. Starting in v0.1.38, the word 'Totals' is added individually in
the methods which call `table_totals` (currently `renderers.HTML.table_pagetotals` and
`renderers.HTML.table_grandtotals`).

Installations which customize any of the `renderers.HTML.table_totals`, `renderers.HTML.table_pagetotals`,
or `renderers.HTML.table_grandtotals` should review the changes to ensure proper functionality.
