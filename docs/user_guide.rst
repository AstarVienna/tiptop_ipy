User Guide
==========

This guide covers the main concepts and features in more detail.

Configuration structure
-----------------------

TIPTOP configurations are organised into sections, each controlling a different
part of the AO simulation:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Section
     - Description
   * - ``atmosphere``
     - Turbulence profile: seeing, outer scale, Cn2 layer heights/weights, wind
   * - ``telescope``
     - Pupil geometry: diameter, obscuration, resolution, static aberrations
   * - ``sources_science``
     - Where and at what wavelength to compute PSFs
   * - ``sources_HO``
     - High-order guide star positions and wavelength
   * - ``sources_LO``
     - Low-order guide star positions and wavelength (optional)
   * - ``sources_Focus``
     - Focus sensor source wavelength (MCAO systems only)
   * - ``sensor_science``
     - Science detector: pixel scale, field of view
   * - ``sensor_HO``
     - High-order wavefront sensor: type, lenslets, photon flux
   * - ``sensor_LO``
     - Low-order wavefront sensor (optional)
   * - ``sensor_Focus``
     - Focus sensor parameters (MCAO systems only)
   * - ``DM``
     - Deformable mirror: actuators, pitch, conjugation altitude
   * - ``RTC``
     - Real-time controller: loop gain, frame rate, delay

For full parameter descriptions, see the
`TIPTOP parameter documentation <https://tiptopdoc.readthedocs.io/en/latest/parameterFile.html>`_.


Tuple indexing
--------------

``TipTop`` uses tuple indexing for clean parameter access:

.. code-block:: python

   # Read
   tt["atmosphere", "Seeing"]          # single value
   tt["atmosphere"]                     # whole section dict

   # Write
   tt["atmosphere", "Seeing"] = 0.6    # single value
   tt["atmosphere"] = {...}             # replace whole section


SCAO vs MCAO systems
---------------------

Single-conjugate AO (SCAO) systems like ERIS, MICADO_SCAO, and SPHERE use a
single guide star and deformable mirror. Their configurations are simpler: no
``sources_LO``, no ``sources_Focus``/``sensor_Focus`` sections.

Multi-conjugate AO (MCAO) systems like MORFEO and MAVIS use multiple laser guide
stars, multiple natural guide stars, and multiple deformable mirrors. Their
configurations include additional sections for low-order and focus sensing.

Both types work identically with ``TipTop`` — the optional sections are simply
absent from SCAO templates.


Multi-wavelength PSFs
---------------------

Request PSFs at multiple wavelengths by providing a list:

.. code-block:: python

   tt["sources_science", "Wavelength"] = [1.2e-6, 1.65e-6, 2.2e-6]
   result = tt.generate_psf()

   result.n_wavelengths  # 3
   j_psf = result.psf_cube(0)  # J-band
   h_psf = result.psf_cube(1)  # H-band
   k_psf = result.psf_cube(2)  # K-band


Multi-position PSFs
-------------------

Request PSFs at multiple field positions:

.. code-block:: python

   tt["sources_science", "Zenith"] = [0, 10, 20]     # arcsec from axis
   tt["sources_science", "Azimuth"] = [0, 90, 180]    # degrees
   result = tt.generate_psf()

   result.x  # cartesian x-coordinates (arcsec)
   result.y  # cartesian y-coordinates (arcsec)

   # Get the PSF nearest to a specific position
   psf = result.nearest_psf(x=5.0, y=0.0)


Plotting
--------

``TipTopResult.plot()`` provides a quick visualisation:

.. code-block:: python

   # Default: log scale, inferno colormap
   result.plot()

   # Linear scale
   result.plot(log_scale=False)

   # Specific wavelength and position
   result.plot(wavelength_index=1, position_index=2)

   # Pass kwargs to imshow
   result.plot(cmap="viridis", vmin=-5, vmax=0)

For more control, access the numpy array directly:

.. code-block:: python

   import matplotlib.pyplot as plt
   from matplotlib.colors import LogNorm

   fig, axes = plt.subplots(1, 3, figsize=(15, 5))
   for i in range(3):
       axes[i].imshow(result.psf_cube(i)[0], norm=LogNorm())
       axes[i].set_title(f"Wavelength {i}")


Reproducibility with diff()
----------------------------

The ``diff()`` method tracks exactly what you changed from the template, making
it easy to document your simulation setup:

.. code-block:: python

   tt = TipTop("MICADO_SCAO")
   tt["atmosphere", "Seeing"] = 0.5
   tt["atmosphere", "L0"] = 30.0
   tt["telescope", "ZenithAngle"] = 45.0

   tt.diff()
   # {'atmosphere': {'Seeing': (0.644, 0.5), 'L0': (25.0, 30.0)},
   #  'telescope': {'ZenithAngle': (0.0, 45.0)}}


Keeping templates up to date
-----------------------------

The ``check_ini_updates.py`` utility syncs instrument templates with the
upstream TIPTOP repository on GitHub:

.. code-block:: bash

   # Check for differences
   python -m tiptop_ipy.check_ini_updates

   # Update local files
   python -m tiptop_ipy.check_ini_updates --update
