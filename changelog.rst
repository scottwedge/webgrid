Changelog
---------


0.1.7 released ???
==================

 - updated filter tests to work with SA0.9

0.1.6 released 2014-05-20
=========================

 -

0.1.5 released 2014-05-20
=========================

 - fix nose plugin setup to avoid warning message
 - fix javascript bug related to sorting & newer jQuery libraries
 - fix SA expression test to avoid boolean ambiguity
 - avoid accidental unicode to text conversion in filters

0.1.4 released 2014-05-18
=========================

  - fix string/unicode handling to avoid coercion of unicode to ascii

0.1.3 released 2014-05-18
=========================

  - adjust the way the Flask blueprint is created and registered
  - adjust route on blueprint so it has /static/... prefix for URL

0.1.0 - 0.1.2 released 2014-05-17
=================================

  - initial release
  - fix packaging issues (0.1.1)
  - adjust init so xlwt not required if not used
