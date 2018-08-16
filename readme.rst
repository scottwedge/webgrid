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

The ``setup.cfg`` file is configured to handle the standard message extraction commands.

To manage the messages in the ``webgrid_ta`` test application:

* ``extract_messages``

  .. code::

     setup.py extract_messages --input-dirs=webgrid_ta --mapping-file=webgrid_ta/i18n/babel.cfg --output-file=webgrid_ta/i18n/webgrid_ta.pot

* ``init_catalog``

  .. code::

     setup.py init_catalog --domain=webgrid_ta --input-file=webgrid_ta/i18n/webgrid_ta.pot --output-dir=webgrid_ta/i18n --locale=es

* ``update_catalog``

  .. code::

     setup.py update_catalog --domain=webgrid_ta --input-file=webgrid_ta/i18n/webgrid_ta.pot --output-dir=webgrid_ta/i18n

* ``compile_catalog``

  .. code::

     setup.py compile_catalog --domain=webgrid_ta --directory=webgrid_ta/i18n
