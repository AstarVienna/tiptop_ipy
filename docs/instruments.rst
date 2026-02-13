Instrument Templates
====================

``tiptop_ipy`` ships with pre-configured templates for several ESO instruments.
These are synced from the upstream
`TIPTOP repository <https://github.com/astro-tiptop/TIPTOP>`_.

Listing available instruments
-----------------------------

.. code-block:: python

   from tiptop_ipy import TipTop
   TipTop.list_instruments()

Available templates
-------------------

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Template
     - Telescope
     - AO Type
     - Description
   * - ``ANDES``
     - ELT (39m)
     - SCAO
     - ArmazoNes high Dispersion Echelle Spectrograph
   * - ``ERIS``
     - VLT (8m)
     - SCAO
     - Enhanced Resolution Imager and Spectrograph
   * - ``ERIS_LGS``
     - VLT (8m)
     - LTAO
     - ERIS with laser guide star
   * - ``HARMONI_SCAO``
     - ELT (39m)
     - SCAO
     - High Angular Resolution Monolithic Optical and Near-infrared IFU
   * - ``HarmoniLTAO_1``
     - ELT (39m)
     - LTAO
     - HARMONI laser tomography mode (config 1)
   * - ``HarmoniLTAO_2``
     - ELT (39m)
     - LTAO
     - HARMONI laser tomography mode (config 2)
   * - ``HarmoniLTAO_3``
     - ELT (39m)
     - LTAO
     - HARMONI laser tomography mode (config 3)
   * - ``MAVIS``
     - VLT (8m)
     - MCAO
     - MCAO Assisted Visible Imager and Spectrograph
   * - ``METIS``
     - ELT (38.5m)
     - SCAO
     - Mid-infrared ELT Imager and Spectrograph
   * - ``MICADO_SCAO``
     - ELT (38.5m)
     - SCAO
     - Multi-AO Imaging Camera for Deep Observations
   * - ``MICADO_SCAO_less_layers``
     - ELT (38.5m)
     - SCAO
     - MICADO with simplified atmosphere (faster)
   * - ``MORFEO``
     - ELT (38.5m)
     - MCAO
     - Multi-conjugate adaptive Optics Relay For ELT Observations
   * - ``MUSE_LTAO``
     - VLT (8m)
     - LTAO
     - Multi Unit Spectroscopic Explorer with laser tomography
   * - ``SOUL``
     - LBT (8.2m)
     - SCAO
     - Single conjugated adaptive Optics Upgrade for LBT
   * - ``SPHERE``
     - VLT (8m)
     - SCAO
     - Spectro-Polarimetric High-contrast Exoplanet REsearch

Usage
-----

Templates are case-insensitive:

.. code-block:: python

   tt = TipTop("ERIS")
   tt = TipTop("eris")       # same thing
   tt = TipTop("ERIS.ini")   # also works

Templates are starting points. You'll typically modify the atmospheric conditions
and science wavelengths to match your observing scenario:

.. code-block:: python

   tt = TipTop("ERIS")
   tt["atmosphere", "Seeing"] = 0.6      # good conditions
   tt["sources_science", "Wavelength"] = [2.2e-6]  # K-band
   result = tt.generate_psf()
