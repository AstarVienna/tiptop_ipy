Changelog
=========

v0.2.0 (unreleased)
--------------------

Major refactoring release.

**New features:**

- ``TipTop`` class (renamed from ``TipTopConnection``) with tuple indexing:
  ``tt["atmosphere", "Seeing"] = 0.6``
- ``TipTopResult`` class wrapping FITS results with ``.psf``, ``.x``, ``.y``
  properties, ``.plot()``, ``.nearest_psf()``, and Jupyter display
- ``diff()`` — see what changed from the template
- ``reset()`` — restore original template values
- ``save()`` / ``load()`` — save and load ``.ini`` files
- ``validate()`` — check config for errors before sending to server
- ``ping()`` — check if the TIPTOP server is reachable
- Case-insensitive instrument template lookup
- Rich Jupyter display (``_repr_html_``) for both ``TipTop`` and ``TipTopResult``
- New instrument templates: HARMONI_SCAO, HarmoniLTAO_2/3, METIS, MUSE_LTAO, SOUL
- ``check_ini_updates.py`` utility for syncing templates with upstream

**Bug fixes:**

- Fixed leading space in TIPTOP server URL
- Fixed INI parser handling of ``=`` in values, ``#`` comments, ``None`` replacement
- Fixed ``list_instruments()`` to return sorted names without ``.ini`` extension

**Breaking changes:**

- ``TipTopConnection`` still works as an alias but ``TipTop`` is the new name
- ``query_server()`` renamed to ``generate_psf()`` (returns ``TipTopResult`` instead of storing on instance)
- ``make_yaml_from_ini()`` / ``make_ini_from_yaml()`` removed from ``utils``
  (replaced by ``ini_parser.parse_ini()`` / ``ini_parser.write_ini()``)

v0.1.0
------

Initial release.
