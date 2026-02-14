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
   :widths: 20 15 10 10 45

   * - Template
     - Telescope
     - AO Type
     - Status
     - Description
   * - ``ANDES``
     - ELT (39m)
     - SCAO
     - |badge-ANDES|
     - ArmazoNes high Dispersion Echelle Spectrograph
   * - ``ERIS``
     - VLT (8m)
     - SCAO
     - |badge-ERIS|
     - Enhanced Resolution Imager and Spectrograph
   * - ``ERIS_LGS``
     - VLT (8m)
     - LTAO
     - |badge-ERIS_LGS|
     - ERIS with laser guide star
   * - ``HARMONI_SCAO``
     - ELT (39m)
     - SCAO
     - |badge-HARMONI_SCAO|
     - High Angular Resolution Monolithic Optical and Near-infrared IFU
   * - ``HarmoniLTAO_1``
     - ELT (39m)
     - LTAO
     - |badge-HarmoniLTAO_1|
     - HARMONI laser tomography mode (config 1)
   * - ``HarmoniLTAO_2``
     - ELT (39m)
     - LTAO
     - |badge-HarmoniLTAO_2|
     - HARMONI laser tomography mode (config 2)
   * - ``HarmoniLTAO_3``
     - ELT (39m)
     - LTAO
     - |badge-HarmoniLTAO_3|
     - HARMONI laser tomography mode (config 3)
   * - ``MAVIS``
     - VLT (8m)
     - MCAO
     - |badge-MAVIS|
     - MCAO Assisted Visible Imager and Spectrograph
   * - ``METIS``
     - ELT (38.5m)
     - SCAO
     - |badge-METIS|
     - Mid-infrared ELT Imager and Spectrograph
   * - ``MICADO_SCAO``
     - ELT (38.5m)
     - SCAO
     - |badge-MICADO_SCAO|
     - Multi-AO Imaging Camera for Deep Observations
   * - ``MICADO_SCAO_less_layers``
     - ELT (38.5m)
     - SCAO
     - |badge-MICADO_SCAO_less_layers|
     - MICADO with simplified atmosphere (faster)
   * - ``MORFEO``
     - ELT (38.5m)
     - MCAO
     - |badge-MORFEO|
     - Multi-conjugate adaptive Optics Relay For ELT Observations
   * - ``MUSE_LTAO``
     - VLT (8m)
     - LTAO
     - |badge-MUSE_LTAO|
     - Multi Unit Spectroscopic Explorer with laser tomography
   * - ``SOUL``
     - LBT (8.2m)
     - SCAO
     - |badge-SOUL|
     - Single conjugated adaptive Optics Upgrade for LBT
   * - ``SPHERE``
     - VLT (8m)
     - SCAO
     - |badge-SPHERE|
     - Spectro-Polarimetric High-contrast Exoplanet REsearch

Configuration summary
---------------------

.. list-table::
   :header-rows: 1
   :widths: 30 15 15 15

   * - INI filename
     - Wavelengths
     - Field of View
     - Cn2 Layers
   * - ``ANDES.ini``
     - 1
     - 512
     - 35
   * - ``ERIS.ini``
     - 1
     - 256
     - 10
   * - ``ERIS_LGS.ini``
     - 1
     - 256
     - 10
   * - ``HARMONI_SCAO.ini``
     - 1
     - 512
     - 10
   * - ``HarmoniLTAO_1.ini``
     - 1
     - 512
     - 10
   * - ``HarmoniLTAO_2.ini``
     - 1
     - 512
     - 10
   * - ``HarmoniLTAO_3.ini``
     - 1
     - 512
     - 10
   * - ``MAVIS.ini``
     - 1
     - 512
     - 10
   * - ``METIS.ini``
     - 1
     - 512
     - 35
   * - ``MICADO_SCAO.ini``
     - 1
     - 512
     - 35
   * - ``MICADO_SCAO_less_layers.ini``
     - 1
     - 512
     - 3
   * - ``MORFEO.ini``
     - 1
     - 512
     - 35
   * - ``MUSE_LTAO.ini``
     - 1
     - 450
     - 10
   * - ``SOUL.ini``
     - 1
     - 256
     - 4
   * - ``SPHERE.ini``
     - 1
     - 256
     - 10

- **Wavelengths**: number of entries in ``sources_science.Wavelength``
- **Field of View**: ``sensor_science.FieldOfView`` (pixels per side), capped at 512 on load
- **Cn2 Layers**: number of entries in ``atmosphere.Cn2Heights``

.. note::

   ``sensor_science.FieldOfView`` is capped at 512 pixels when loading
   templates or INI files.  Larger values cause the ESO server to time out.
   You can override this after loading::

      tt = TipTop("MICADO_SCAO")
      tt["sensor_science", "FieldOfView"] = 2048  # at your own risk

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

.. |badge-ANDES| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/ANDES.json
   :alt: ANDES status

.. |badge-ERIS| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/ERIS.json
   :alt: ERIS status

.. |badge-ERIS_LGS| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/ERIS_LGS.json
   :alt: ERIS_LGS status

.. |badge-HARMONI_SCAO| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/HARMONI_SCAO.json
   :alt: HARMONI_SCAO status

.. |badge-HarmoniLTAO_1| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/HarmoniLTAO_1.json
   :alt: HarmoniLTAO_1 status

.. |badge-HarmoniLTAO_2| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/HarmoniLTAO_2.json
   :alt: HarmoniLTAO_2 status

.. |badge-HarmoniLTAO_3| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/HarmoniLTAO_3.json
   :alt: HarmoniLTAO_3 status

.. |badge-MAVIS| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/MAVIS.json
   :alt: MAVIS status

.. |badge-METIS| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/METIS.json
   :alt: METIS status

.. |badge-MICADO_SCAO| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/MICADO_SCAO.json
   :alt: MICADO_SCAO status

.. |badge-MICADO_SCAO_less_layers| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/MICADO_SCAO_less_layers.json
   :alt: MICADO_SCAO_less_layers status

.. |badge-MORFEO| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/MORFEO.json
   :alt: MORFEO status

.. |badge-MUSE_LTAO| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/MUSE_LTAO.json
   :alt: MUSE_LTAO status

.. |badge-SOUL| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/SOUL.json
   :alt: SOUL status

.. |badge-SPHERE| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/AstarVienna/tiptop_ipy/main/status/badges/SPHERE.json
   :alt: SPHERE status
