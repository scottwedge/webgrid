Changelog
=========

0.1.42 released 2019-05-13
--------------------------

- Ensure session store maintains proper data type through load/save (#35) (e7c5bdf_)

.. _e7c5bdf: https://github.com/level12/webgrid/commit/e7c5bdf


0.1.41 released 2019-03-25
--------------------------

- Fix warning from xlsxwriter when second column has a subtotal (05e0663_)

.. _05e0663: https://github.com/level12/webgrid/commit/05e0663


0.1.40 released 2019-02-18
--------------------------

- py3: Fix Deprecation Warning for Inspect Call (#53) (9c87cc4_)

.. _9c87cc4: https://github.com/level12/webgrid/commit/9c87cc4


0.1.39 released 2019-01-03
--------------------------

- Properly handle None in date filter "between" ops (4da6069_)

.. _4da6069: https://github.com/level12/webgrid/commit/4da6069


0.1.38 released 2018-11-14
--------------------------

- Add optional i18n support using morphi (3627e8f_)
  NOTE: there is a slight change that could result in a behavioral change during
  upgrade! Please see the 'Upgrading' section in the readme for more
  information!

.. _3627e8f: https://github.com/level12/webgrid/commit/3627e8f


0.1.37 released 2018-09-10
--------------------------

- XLSX formats are cached for performance

0.1.36 released 2018-08-09
--------------------------

- Add test helper `assert_rendered_xls_matches` in `webgrid.testing`
- Add support for XLSX, and CSV renderers
  - If you have xlsxwriter installed, xlsx export link will appear
- DEPRECATED old export mechanism
  - If you are calling `g.xls.as_response()` please replace that with 
  `g.export_as_response()` which will select the correct renderer and return
  the response correctly
  - If xlsx is enabled you will need to make this above change to enable xlsx exporting

0.1.35 released 2018-01-05
--------------------------

 - fix CSS collision in tr classes with Bootstrap
 - change multiselect to use body as the container for the multiselect list

0.1.34 released 2017-08-25
--------------------------

 - session_override GET arg added to allow patching additional operators into the session (rather than overriding session filters)

0.1.33 released 2017-06-13
--------------------------

 - limit XLS sheet names to 30 characters, per the Excel format limit

0.1.32 released 2017-06-09
--------------------------

 - corrected the results of Filter.is_active to account for default operation with no value
 - fixed formencode requirement for python 3
 - update options filter error to include class name

0.1.31 released 2016-11-03
--------------------------

 - corrected DateTimeFilter processing to avoid "invalid date" messages

0.1.30 released 2016-10-28
--------------------------

 - fixed problem with lambda default args being processed by the grid

0.1.29 released 2016-10-28
--------------------------

 - allow default operation passed to filter to be a callable

0.1.28 released 2016-10-13
--------------------------

 - fixed an additional regression in DateFilter and DateTimeFilter validation

0.1.27 released 2016-10-13
--------------------------

 - corrected DateFilter and DateTimeFilter operations for empty, not empty, and between

0.1.26 released 2016-10-03
--------------------------

 - update TextFilter to support case-insensitive operations for dialects like postgresql and sqlite

0.1.25 released 2016-09-12
--------------------------

 - various bug fixes in DateTimeFilter
 - introduce support for Arrow date objects in grid and date filters

0.1.24 released 2016-05-10
--------------------------

 - enhanced options for subtotals to include sum, avg, strings, and SQLAlchemy expressions

0.1.23 released 2016-04-18
--------------------------

 - change dependency to webhelpers2 from webhelpers
 - update to support new python-dateutil, including fix of old parsing exception
 - fix testing compatibility with Flask-SQLALchemy 2.1
 - fix testing dependencies problem in setup
 - support Python 3.4 and newer

0.1.22 released 2016-02-18
--------------------------

 - fix potential warnings for SQLAlchemy when sorting by a label instead of an SA expression

0.1.21 released 2016-02-18
--------------------------

 - bad release

0.1.20 released 2016-02-18
--------------------------

 - errant release, identical to 0.1.19

0.1.19 released 2016-02-16
--------------------------

 - fix edit/delete link display on large screens

0.1.18 released 2015-12-11
--------------------------

 - fix bugs related to default operations using no-input date filters

0.1.17 released 2015-12-04
--------------------------

 - add YesNoFilter and OptionsIntFilterBase helper
 - fix compatibility with SQLAlchemy 1.0.9 for tests to pass
 - add additional DateFilter operators

0.1.16 released 2015-10-15
--------------------------

 - fixed problem with possible date/datetime filter overflows

0.1.15 released 2015-07-02
--------------------------

 - add time column and filter

0.1.14 released 2015-05-11
--------------------------

 - fix problem where empty strings passed to set as a non-required value 2 causes validation error

0.1.13 released 2015-02-12
--------------------------

 - attempt to use column label for subtotaling if no SA expression is provided
 - allow callers to specify default arguments to filters

0.1.12 released 2014-11-18
--------------------------

 - allow filters to set additional html attributes on their table rows

0.1.11 released 2014-10-09
--------------------------

 - fixed setup to include only webgrid in install, without the test apps

0.1.10 released 2014-10-02
--------------------------

 - bug fix: hide_controls_box grid attribute used in rendering

0.1.9 released 2014-09-22
-------------------------

 - bug fix: corrected default_op processing on TextFilter

0.1.8 released 2014-09-22
-------------------------

 - enable default_op processing for all filter types

0.1.7 released 2014-09-18
-------------------------

 - BC break: replaced MultiSelect widget with multipleSelect plugin.
   Related JS and CSS must be included (available in webgrid static)
 - included missing images referenced by webgrid CSS

0.1.6 released 2014-08-22
-------------------------

 - updated filter tests to work with SA0.9
 - refactoring related to subtotaling feature
 - adjustments for SQLAlchemy 0.9+ (we now support 0.8+)
 - workaround for dateutils parsing bug
 - testing fixes
 - completed dev requirements list
 - fixed nose plugin bug, must not assume pathname case consistency (Windows)
 - added BlazeWeb adapter
 - xls_as_response now an adapter method, called by XLS renderer
 - render_template now an optional adapter method, falls back to Jinja2 call

0.1.5 released 2014-05-20
-------------------------

 - fix nose plugin setup to avoid warning message
 - fix javascript bug related to sorting & newer jQuery libraries
 - fix SA expression test to avoid boolean ambiguity
 - avoid accidental unicode to text conversion in filters

0.1.4 released 2014-05-18
-------------------------

  - fix string/unicode handling to avoid coercion of unicode to ascii

0.1.3 released 2014-05-18
-------------------------

  - adjust the way the Flask blueprint is created and registered
  - adjust route on blueprint so it has /static/... prefix for URL

0.1.0 - 0.1.2 released 2014-05-17
---------------------------------

  - initial release
  - fix packaging issues (0.1.1)
  - adjust init so xlwt not required if not used
