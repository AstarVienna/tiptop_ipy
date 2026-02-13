tiptop_ipy
==========

A Python wrapper for the `ESO TIPTOP <https://tiptopdoc.readthedocs.io/>`_
adaptive optics PSF simulation microservice — designed for IPython and Jupyter
workflows.

``tiptop_ipy`` lets you configure AO system parameters, send them to the ESO
TIPTOP server, and work with the resulting PSFs, all from a notebook or script.

.. code-block:: python

   from tiptop_ipy import TipTop

   tt = TipTop("MICADO_SCAO")
   tt["atmosphere", "Seeing"] = 0.6
   result = tt.generate_psf()
   result.plot()

.. toctree::
   :maxdepth: 2
   :caption: Contents

   installation
   quickstart
   user_guide
   instruments
   api

.. toctree::
   :maxdepth: 1
   :caption: Development

   changelog
